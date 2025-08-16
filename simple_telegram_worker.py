"""
Simple Telegram worker for sending notifications
Based on VS5 telegram worker, adapted for Kufar.by items
"""

import logging
import time
import asyncio
from typing import List, Dict, Any, Optional
from telegram import Bot, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError, RetryAfter, TimedOut
from telegram.constants import ParseMode

from db import db
from configuration_values import get_telegram_bot_token, get_telegram_chat_id

logger = logging.getLogger(__name__)

class TelegramWorker:
    """Handles sending Telegram notifications for new Kufar items"""
    
    def __init__(self, bot_token: str = None):
        if not bot_token:
            bot_token = get_telegram_bot_token()
        if not bot_token:
            raise ValueError("Telegram bot token is required")
        
        self.bot = Bot(token=bot_token)
        self.max_retries = 3
        self.retry_delay = 5
    
    async def send_item_notification(self, item: Dict[str, Any]) -> bool:
        """Send notification about new item"""
        try:
            # Get chat_id from configuration
            chat_id = get_telegram_chat_id()
            thread_id = item.get('telegram_thread_id') or item.get('thread_id')
            
            # Debug thread_id routing
            search_name = item.get('search_name', 'Unknown')
            logger.info(f"🎯 Routing item '{search_name}' - Chat: {chat_id}, Thread: {thread_id}")
            logger.info(f"🔍 Available item keys: {list(item.keys())}")
            
            if not chat_id:
                logger.warning(f"No telegram chat_id configured for notifications")
                return False
            
            # Format message
            message = self._format_item_message(item)
            
            # Create inline keyboard with "Open Kufar" button
            keyboard = None
            url = item.get('url', '')
            logger.info(f"🔗 Item URL: {url}")
            if url:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Open Kufar", url=url)]
                ])
                logger.info(f"✅ Created keyboard with button: Open Kufar -> {url}")
            else:
                logger.warning("❌ No URL found for item - button will not be created")
            
            # SIMPLIFIED APPROACH - ALWAYS USE send_photo WITH BUTTON
            images = item.get('images', [])
            
            # Always send as photo, even if no image (use placeholder)
            photo_url = images[0] if images else "https://via.placeholder.com/300x300/cccccc/666666?text=No+Image"
            
            logger.info(f"📷 SIMPLIFIED: Sending photo with button to chat {chat_id}")
            logger.info(f"🔍 DEBUG: keyboard exists={keyboard is not None}")
            logger.info(f"🔍 DEBUG: photo_url={photo_url}")
            logger.info(f"🔍 DEBUG: message={message[:100]}...")
            
            # Use bot.send_photo directly with all parameters
            try:
                kwargs = {
                    'chat_id': chat_id,
                    'photo': photo_url,
                    'caption': message,
                    'parse_mode': ParseMode.HTML
                }
                
                if thread_id:
                    kwargs['message_thread_id'] = int(thread_id)
                    logger.info(f"🎯 Adding thread_id: {thread_id}")
                
                if keyboard:
                    kwargs['reply_markup'] = keyboard
                    logger.info(f"🔧 Adding keyboard: {keyboard}")
                else:
                    logger.warning("❌ No keyboard - button will be missing!")
                
                logger.info(f"📤 DIRECT send_photo call with: {list(kwargs.keys())}")
                await self.bot.send_photo(**kwargs)
                logger.info("✅ DIRECT send_photo SUCCESS!")
                success = True
                
            except Exception as e:
                logger.error(f"❌ DIRECT send_photo FAILED: {e}")
                success = False
            
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
            
            # Extract size from description or raw_data if available
            size = ""
            description = item.get('description', '')
            raw_data = item.get('raw_data', {})
            
            # Try to extract size from various sources
            if isinstance(raw_data, dict):
                size = raw_data.get('size', '') or raw_data.get('параметры', {}).get('размер', '')
            
            # If no size found, try to extract from description
            if not size and description:
                import re
                # Look for size patterns like "48 (M)", "M", "Large", etc.
                size_patterns = [
                    r'размер\s+(\d+\s*\([XSMLXL]+\))',  # размер 48 (M)
                    r'размер\s+([XSMLXL]{1,3})\b',      # размер M, XL, XXL
                    r'размер\s+(\d{2,3})\b',            # размер 48
                    r'в\s+размере\s+([XSMLXL]{1,3})\b', # в размере XXL
                    r'в\s+размере\s+(\d{2,3})\b',       # в размере 48
                    r'size\s+([XSMLXL]{1,3})\b',        # size XL
                    r'\b(\d+\s*\([XSMLXL]+\))',         # 48 (M)
                    r'\b([XSMLXL]{1,3})\b',             # M, XL, XXL (standalone)
                    r'\b(\d{2,3})\s*размер',            # 48 размер
                    r'\b(large|medium|small)\b',        # Large, Medium, Small
                ]
                for pattern in size_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        size = match.group(1)
                        break
            
            # Format price
            if price > 0:
                price_text = f"<b>{price:,} {currency}</b>".replace(',', ' ')
            else:
                price_text = "<b>Цена не указана</b>"
            
            # Build message
            message_parts = [
                f"🔍 {search_name}",
                "",
                f"<b>{title}</b>",
                f"💶 {price_text}",
            ]
            
            # Add size if available
            if size:
                message_parts.append(f"⛓️ {size}")
            
            # Add location
            if location and location.strip():
                message_parts.append(f"{location}")
            # Skip location if not available (cleaner message)
            
            return "\n".join(message_parts)
            
        except Exception as e:
            logger.error(f"Error formatting message: {e}")
            return f"Новое объявление: {item.get('title', 'Без названия')}"
    
    async def _send_single_photo_with_button(self, chat_id: str, thread_id: str = None, 
                                           message: str = "", photo_url: str = "", reply_markup=None) -> bool:
        """Send single photo with caption and inline button"""
        for attempt in range(self.max_retries):
            try:
                kwargs = {
                    'chat_id': chat_id,
                    'photo': photo_url,
                    'caption': message,
                    'parse_mode': ParseMode.HTML
                }
                
                if thread_id:
                    kwargs['message_thread_id'] = int(thread_id)
                    logger.info(f"🎯 Setting photo message_thread_id to: {thread_id}")
                else:
                    logger.info(f"🎯 No thread_id for photo - sending to main chat")
                
                if reply_markup:
                    kwargs['reply_markup'] = reply_markup
                    logger.info(f"🔧 Adding reply_markup to photo: {type(reply_markup)}")
                else:
                    logger.info("🔧 No reply_markup provided for photo")
                
                logger.info(f"📤 Sending photo with kwargs: {list(kwargs.keys())}")
                await self.bot.send_photo(**kwargs)
                logger.info("✅ Photo with button sent successfully!")
                return True
                
            except RetryAfter as e:
                logger.warning(f"Rate limited, waiting {e.retry_after} seconds")
                await asyncio.sleep(e.retry_after)
                
            except TimedOut:
                logger.warning(f"Telegram timeout, attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    
            except Exception as e:
                logger.error(f"Failed to send photo with button (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        
        logger.error("Failed to send photo with button after all retries")
        return False
    
    async def _send_text_message(self, chat_id: str, thread_id: str = None, message: str = "", reply_markup=None) -> bool:
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
                    logger.info(f"🎯 Setting message_thread_id to: {thread_id}")
                else:
                    logger.info(f"🎯 No thread_id provided - sending to main chat")
                
                if reply_markup:
                    kwargs['reply_markup'] = reply_markup
                    logger.info(f"🔧 Adding reply_markup to message: {type(reply_markup)}")
                else:
                    logger.info("🔧 No reply_markup provided")
                
                logger.info(f"📤 Sending message with kwargs: {list(kwargs.keys())}")
                await self.bot.send_message(**kwargs)
                logger.info("✅ Message sent successfully!")
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
                               message: str = "", images: List[str] = None, reply_markup=None) -> bool:
        """Send message with images as media group - DEPRECATED! Should not be called!"""
        logger.error("🚨 DEPRECATED _send_with_images called! This should not happen!")
        if not images:
            return await self._send_text_message(chat_id, thread_id, message, reply_markup)
        
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
                    logger.info(f"🎯 Setting media group message_thread_id to: {thread_id}")
                else:
                    logger.info(f"🎯 No thread_id for media group - sending to main chat")
                
                logger.info(f"📤 Sending media group with kwargs: {list(kwargs.keys())}")
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
                    return await self._send_text_message(chat_id, thread_id, message, reply_markup)
                
                if "chat not found" in str(e).lower():
                    return False
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
            
            except Exception as e:
                logger.error(f"Unexpected error sending media: {e}")
                # Try fallback to text only
                return await self._send_text_message(chat_id, thread_id, message, reply_markup)
        
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

def send_notification_for_item(item: Dict[str, Any]) -> bool:
    """Send notification for a single item (synchronous)"""
    try:
        if not get_telegram_bot_token():
            logger.error("Telegram bot token not configured")
            return False
        
        worker = TelegramWorker()
        
        # Run async function synchronously
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(worker.send_item_notification(item))
        return result
        
    except Exception as e:
        logger.error(f"Error sending notification for item: {e}")
        return False

# Async wrapper for synchronous usage
def send_notifications():
    """Synchronous wrapper for sending notifications"""
    try:
        if not get_telegram_bot_token():
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
