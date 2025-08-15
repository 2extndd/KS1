"""
Simple Telegram worker for sending notifications
Based on VS5 telegram worker, adapted for Kufar.by items
"""

import logging
import time
import asyncio
from typing import List, Dict, Any, Optional
from telegram import Bot, InputMediaPhoto
from telegram.error import TelegramError, RetryAfter, TimedOut
from telegram.constants import ParseMode

from db import db
from configuration_values import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

class TelegramWorker:
    """Handles sending Telegram notifications for new Kufar items"""
    
    def __init__(self, bot_token: str = TELEGRAM_BOT_TOKEN):
        if not bot_token:
            raise ValueError("Telegram bot token is required")
        
        self.bot = Bot(token=bot_token)
        self.max_retries = 3
        self.retry_delay = 5
    
    async def send_item_notification(self, item: Dict[str, Any]) -> bool:
        """Send notification about new item"""
        try:
            chat_id = item.get('telegram_chat_id')
            thread_id = item.get('telegram_thread_id')
            
            if not chat_id:
                logger.warning(f"No chat_id for item {item['id']}")
                return False
            
            # Format message
            message = self._format_item_message(item)
            
            # Prepare images
            images = item.get('images', [])
            
            if images:
                # Send with images
                success = await self._send_with_images(
                    chat_id=chat_id,
                    thread_id=thread_id,
                    message=message,
                    images=images[:10]  # Telegram limit: 10 photos per album
                )
            else:
                # Send text only
                success = await self._send_text_message(
                    chat_id=chat_id,
                    thread_id=thread_id,
                    message=message
                )
            
            if success:
                # Mark item as sent
                db.mark_item_sent(item['id'])
                logger.info(f"Sent notification for item {item['kufar_id']}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send notification for item {item['id']}: {e}")
            return False
    
    def _format_item_message(self, item: Dict[str, Any]) -> str:
        """Format item data into Telegram message"""
        try:
            # Basic info
            title = item.get('title', 'Без названия')
            price = item.get('price', 0)
            currency = item.get('currency', 'BYN')
            location = item.get('location', '')
            url = item.get('url', '')
            search_name = item.get('search_name', '')
            
            # Format price
            if price > 0:
                price_text = f"{price:,} {currency}".replace(',', ' ')
            else:
                price_text = "Цена не указана"
            
            # Build message
            message_parts = [
                f"🔍 <b>{search_name}</b>",
                "",
                f"📦 <b>{title}</b>",
                f"💰 {price_text}",
            ]
            
            if location:
                message_parts.append(f"📍 {location}")
            
            # Add seller info if available
            seller_name = item.get('seller_name', '')
            if seller_name:
                message_parts.append(f"👤 {seller_name}")
            
            # Add description preview (first 200 chars)
            description = item.get('description', '')
            if description:
                desc_preview = description[:200]
                if len(description) > 200:
                    desc_preview += "..."
                message_parts.extend(["", f"📝 {desc_preview}"])
            
            # Add URL
            if url:
                message_parts.extend(["", f"🔗 <a href='{url}'>Открыть на Kufar</a>"])
            
            return "\n".join(message_parts)
            
        except Exception as e:
            logger.error(f"Error formatting message: {e}")
            return f"Новое объявление: {item.get('title', 'Без названия')}"
    
    async def _send_text_message(self, chat_id: str, thread_id: str = None, message: str = "") -> bool:
        """Send text-only message"""
        for attempt in range(self.max_retries):
            try:
                kwargs = {
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': ParseMode.HTML,
                    'disable_web_page_preview': True
                }
                
                if thread_id:
                    kwargs['message_thread_id'] = int(thread_id)
                
                await self.bot.send_message(**kwargs)
                return True
                
            except RetryAfter as e:
                logger.warning(f"Rate limited, waiting {e.retry_after} seconds")
                await asyncio.sleep(e.retry_after)
                
            except TimedOut:
                logger.warning(f"Telegram timeout, attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                
            except TelegramError as e:
                logger.error(f"Telegram error: {e}")
                if "chat not found" in str(e).lower():
                    return False  # Don't retry for invalid chats
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
            
            except Exception as e:
                logger.error(f"Unexpected error sending message: {e}")
                return False
        
        return False
    
    async def _send_with_images(self, chat_id: str, thread_id: str = None, 
                               message: str = "", images: List[str] = None) -> bool:
        """Send message with images as media group"""
        if not images:
            return await self._send_text_message(chat_id, thread_id, message)
        
        for attempt in range(self.max_retries):
            try:
                # Prepare media group
                media = []
                for i, image_url in enumerate(images):
                    if i == 0:
                        # First image gets the caption
                        media.append(InputMediaPhoto(
                            media=image_url,
                            caption=message,
                            parse_mode=ParseMode.HTML
                        ))
                    else:
                        media.append(InputMediaPhoto(media=image_url))
                
                kwargs = {
                    'chat_id': chat_id,
                    'media': media
                }
                
                if thread_id:
                    kwargs['message_thread_id'] = int(thread_id)
                
                await self.bot.send_media_group(**kwargs)
                return True
                
            except RetryAfter as e:
                logger.warning(f"Rate limited, waiting {e.retry_after} seconds")
                await asyncio.sleep(e.retry_after)
                
            except TimedOut:
                logger.warning(f"Telegram timeout, attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                
            except TelegramError as e:
                logger.error(f"Telegram error sending media: {e}")
                
                # If media group fails, try sending text only
                if "media group" in str(e).lower() or "photo" in str(e).lower():
                    logger.info("Media group failed, sending text only")
                    return await self._send_text_message(chat_id, thread_id, message)
                
                if "chat not found" in str(e).lower():
                    return False
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
            
            except Exception as e:
                logger.error(f"Unexpected error sending media: {e}")
                # Try fallback to text only
                return await self._send_text_message(chat_id, thread_id, message)
        
        return False
    
    async def send_system_message(self, chat_id: str, message: str, thread_id: str = None) -> bool:
        """Send system/status message"""
        try:
            formatted_message = f"🤖 <b>KF Searcher</b>\n\n{message}"
            return await self._send_text_message(chat_id, thread_id, formatted_message)
        except Exception as e:
            logger.error(f"Failed to send system message: {e}")
            return False
    
    async def process_pending_notifications(self) -> Dict[str, Any]:
        """Process all pending notifications"""
        logger.info("Processing pending Telegram notifications")
        
        results = {
            'total_items': 0,
            'sent_successfully': 0,
            'failed_items': 0,
            'errors': []
        }
        
        try:
            # Get unsent items
            unsent_items = db.get_unsent_items()
            results['total_items'] = len(unsent_items)
            
            if not unsent_items:
                logger.info("No pending notifications")
                return results
            
            # Process each item
            for item in unsent_items:
                try:
                    success = await self.send_item_notification(item)
                    
                    if success:
                        results['sent_successfully'] += 1
                    else:
                        results['failed_items'] += 1
                        results['errors'].append({
                            'item_id': item['id'],
                            'error': 'Failed to send notification'
                        })
                    
                    # Small delay between messages to avoid rate limits
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing item {item['id']}: {e}")
                    results['failed_items'] += 1
                    results['errors'].append({
                        'item_id': item['id'],
                        'error': str(e)
                    })
            
            logger.info(f"Notification processing completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error in process_pending_notifications: {e}")
            results['errors'].append({'error': str(e)})
            return results

# Async wrapper for synchronous usage
def send_notifications():
    """Synchronous wrapper for sending notifications"""
    try:
        if not TELEGRAM_BOT_TOKEN:
            logger.error("Telegram bot token not configured")
            return {'error': 'Bot token not configured'}
        
        worker = TelegramWorker()
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(worker.process_pending_notifications())
            return results
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in send_notifications: {e}")
        return {'error': str(e)}
