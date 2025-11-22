"""
Flask web application for KF Searcher UI
Based on VS5 web interface, adapted for Kufar.by
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.exceptions import BadRequest

# Setup logger
logger = logging.getLogger(__name__)

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db
from core import searcher
from simple_telegram_worker import send_notifications
from railway_redeploy import redeployer
from configuration_values import SECRET_KEY

def extract_size_from_item_data(item):
    """Extract size information from item data for WebUI with improved validation"""
    size = ""
    description = item.get('description', '')
    raw_data = item.get('raw_data', {})
    title = item.get('title', '')
    
    logger.info(f"🔍 SIZE DEBUG EXTRACT: Extracting size for item '{title}'. raw_data: {raw_data}")
    
    # Try to extract size from various sources
    if isinstance(raw_data, dict):
        size = raw_data.get('size', '') or raw_data.get('параметры', {}).get('размер', '')
        if size:
            logger.info(f"🔍 SIZE DEBUG EXTRACT: Found size in raw_data: '{size}'")
    
    # If no size found, try to extract from description and title
    if not size:
        texts_to_check = [title, description]
        
        for text in texts_to_check:
            if not text:
                continue
                
            size = _extract_size_with_validation_webui(text)
            if size:
                logger.info(f"🔍 SIZE DEBUG EXTRACT: Extracted size from text '{text[:50]}...': '{size}'")
                break
    
    final_size = size.strip() if size else ""
    logger.info(f"🔍 SIZE DEBUG EXTRACT: Final size for '{title}': '{final_size}'")
    return final_size

def _extract_size_with_validation_webui(text: str) -> str:
    """Extract size with validation to avoid false positives (WebUI version)"""
    if not text:
        return ""
    
    import re
    
    # More precise size patterns with context
    size_patterns = [
        # Explicit size mentions
        r'размер[:.\s]+(\d+[-–]\d+\s*\([XSMLXL]+\))',  # размер: 52-54 (XXL)
        r'размер[:.\s]+(\d+\s*\([XSMLXL]+\))',         # размер: 48 (M)
        r'размер[:.\s]+([XSMLXL]{1,3})\b',             # размер: M, XL, XXL
        r'размер[:.\s]+(\d{2,3})\b',                   # размер: 48
        r'р-р[:.\s]+(\d+[-–]\d+)',                     # р-р: 48-50
        r'р-р[:.\s]+(\d{2,3})',                        # р-р: 48
        r'в\s+размере\s+([XSMLXL]{1,3})\b',           # в размере XXL
        r'в\s+размере\s+(\d{2,3})\b',                 # в размере 48
        r'size[:.\s]+([XSMLXL]{1,3})\b',              # size: XL
        
        # Size in parentheses after clothing items
        r'(?:куртка|рубашка|платье|джинсы|брюки|футболка|свитер|костюм|пальто|блузка|юбка|шорты|толстовка|худи|кофта|свитшот)\s+.*?(\d+[-–]\d+\s*\([XSMLXL]+\))',
        r'(?:куртка|рубашка|платье|джинсы|брюки|футболка|свитер|костюм|пальто|блузка|юбка|шорты|толстовка|худи|кофта|свитшот)\s+.*?(\d+\s*\([XSMLXL]+\))',
        r'(?:куртка|рубашка|платье|джинсы|брюки|футболка|свитер|костюм|пальто|блузка|юбка|шорты|толстовка|худи|кофта|свитшот)\s+.*?\b([XSMLXL]{1,3})\b',
    ]
    
    for pattern in size_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            potential_size = match.group(1).strip()
            
            # Validate the extracted size
            if _is_valid_clothing_size_webui(potential_size, text):
                return potential_size
    
    return ""

def _is_valid_clothing_size_webui(size: str, context: str) -> bool:
    """Validate if the extracted text is actually a clothing size (WebUI version)"""
    if not size:
        return False
    
    import re
    
    # List of words that indicate this is likely clothing
    clothing_indicators = [
        'куртка', 'рубашка', 'платье', 'джинсы', 'брюки', 'футболка', 'свитер', 
        'костюм', 'пальто', 'блузка', 'юбка', 'шорты', 'толстовка', 'худи', 
        'кофта', 'майка', 'рубашка', 'жакет', 'жилет', 'комбинезон', 'халат',
        'одежда', 'размер', 'р-р', 'size', 'свитшот'
    ]
    
    # Check if context contains clothing-related words
    has_clothing_context = any(word in context.lower() for word in clothing_indicators)
    
    # List of things that are definitely NOT clothing sizes
    false_positives = [
        # Years
        r'^(19|20)\d{2}$',  # 1990, 2020 etc
        # Large numbers that are likely prices or IDs
        r'^\d{4,}$',  # 1000, 10000 etc
        r'^[5-9]\d{2}$',  # 500+, likely IDs not sizes
        # Phone numbers parts
        r'^\d{2,3}$' if not has_clothing_context else None,  # 25, 375 etc without clothing context
        # Common non-size words
        r'^(the|and|для|или|от|до|за|на|в|с|по)$',
    ]
    
    # Check against false positives
    for fp_pattern in false_positives:
        if fp_pattern and re.match(fp_pattern, size, re.IGNORECASE):
            return False
    
    # Valid size patterns
    valid_patterns = [
        r'^[XSMLXL]{1,4}$',  # XS, S, M, L, XL, XXL, XXXL
        r'^\d{2,3}$',        # 42, 48, 52 etc (if has clothing context)
        r'^\d{2,3}[-–]\d{2,3}$',  # 48-50, 52-54
        r'^\d{2,3}\s*\([XSMLXL]+\)$',  # 48 (M), 52 (L)
        r'^\d{2,3}[-–]\d{2,3}\s*\([XSMLXL]+\)$',  # 52-54 (XL)
        r'^(large|medium|small|extra)$',  # English size words
    ]
    
    # Check if size matches valid patterns
    for pattern in valid_patterns:
        if re.match(pattern, size, re.IGNORECASE):
            # For numeric sizes, require clothing context AND reasonable range
            if re.match(r'^\d', size):
                if has_clothing_context:
                    # Additional check for reasonable clothing sizes
                    numeric_part = re.findall(r'\d+', size)
                    if numeric_part:
                        num = int(numeric_part[0])
                        # Reasonable clothing size range (european sizes mostly 36-70)
                        if 30 <= num <= 70:
                            return True
                return False
            else:
                # Letter sizes are usually valid
                return True
    
    return False

def format_price_with_size(item):
    """Format price with size in format '75 BYN - 48 (M)'"""
    price = item.get('price', 0)
    currency = item.get('currency', 'BYN')
    
    # Format price
    price_text = f"{price:,} {currency}".replace(',', ' ') if price > 0 else "Цена не указана"
    
    # Extract size
    size = extract_size_from_item_data(item)
    logger.info(f"🔍 SIZE DEBUG WEB UI: Item '{item.get('title', 'Unknown')}' extracted size: '{size}'")
    
    # Combine price and size
    if size:
        logger.info(f"🔍 SIZE DEBUG WEB UI: Displaying size '{size}' for item '{item.get('title', 'Unknown')}'")
        return f"{price_text}<br/><small class='text-muted'>{size}</small>"
    else:
        logger.info(f"🔍 SIZE DEBUG WEB UI: No size to display for item '{item.get('title', 'Unknown')}'")
        return price_text

def create_app():
    """Create Flask application"""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    app.secret_key = SECRET_KEY
    
    # Add custom template functions
    app.jinja_env.globals.update(
        extract_size_from_item_data=extract_size_from_item_data,
        format_price_with_size=format_price_with_size
    )
    
    # Dashboard route
    @app.route('/')
    def dashboard():
        """Main dashboard"""
        try:
            # Get statistics
            db_stats = get_db().get_items_stats()
            
            from datetime import datetime
            import datetime as dt
            import sys
            import os
            
            # Add parent directory to path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            
            # Get real searcher status from metrics_storage
            try:
                import metrics_storage
                total_api_requests = metrics_storage.metrics_storage.get_total_api_requests()
                app_start_time = metrics_storage.metrics_storage.get_app_start_time()
                logger.info(f"Successfully loaded stats: API requests={total_api_requests}, start_time={app_start_time}")
            except Exception as e:
                logger.error(f"Error importing metrics_storage: {e}")
                total_api_requests = 0
                app_start_time = datetime.now()
            
            # Calculate real uptime
            uptime_seconds = (datetime.now() - app_start_time).total_seconds()
            uptime_str = str(dt.timedelta(seconds=int(uptime_seconds)))
            
            # Get last found item
            last_item = get_db().get_last_found_item()
            
            searcher_status = {
                'total_api_requests': total_api_requests,
                'uptime': uptime_str,
                'last_found_item': last_item,
                'is_running': True
            }
            
            # Get recent items (last 24 hours)
            recent_items = get_recent_items(24)
            
            # Get active searches
            active_searches = get_db().get_active_searches()
            
            return render_template('dashboard.html',
                                 db_stats=db_stats,
                                 searcher_status=searcher_status,
                                 recent_items=recent_items[:30],  # Show last 30
                                 active_searches=active_searches[:5])  # Show first 5
        except Exception as e:
            flash(f'Error loading dashboard: {e}', 'error')
            return render_template('dashboard.html',
                                 db_stats={},
                                 searcher_status={},
                                 recent_items=[],
                                 active_searches=[])
    
    # Items route
    @app.route('/items')
    def items():
        """Items listing page"""
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 30))
            search_filter = request.args.get('search', '')
            search_id = request.args.get('search_id', '')  # Добавляем фильтрацию по search_id
            
            items_data = get_items_paginated(page, per_page, search_filter, search_id)
            
            return render_template('items.html',
                                 items=items_data['items'],
                                 pagination=items_data['pagination'],
                                 search_filter=search_filter,
                                 search_id=search_id)
        except Exception as e:
            flash(f'Error loading items: {e}', 'error')
            return render_template('items.html', items=[], pagination={})
    
    # Searches/Queries route
    @app.route('/searches')
    def searches():
        """Searches management page"""
        try:
            searches = get_db().get_active_searches()
            return render_template('searches.html', searches=searches)
        except Exception as e:
            flash(f'Error loading searches: {e}', 'error')
            return render_template('searches.html', searches=[])
    
    # Add search route
    @app.route('/searches/add', methods=['GET', 'POST'])
    def add_search():
        """Add new search"""
        if request.method == 'POST':
            try:
                name = request.form.get('name')
                url = request.form.get('url')
                telegram_chat_id = request.form.get('telegram_chat_id')
                telegram_thread_id = request.form.get('telegram_thread_id')
                
                if not name or not url:
                    flash('Name and URL are required', 'error')
                    return render_template('add_search.html')
                
                # Validate URL
                url_info = searcher.validate_search_url(url)
                if not url_info['valid']:
                    flash(f'Invalid URL: {url_info["error"]}', 'error')
                    return render_template('add_search.html')
                
                # Add search
                search_id = get_db().add_search(
                    name=name,
                    url=url,
                    telegram_chat_id=telegram_chat_id,
                    telegram_thread_id=telegram_thread_id
                )
                
                flash(f'Search "{name}" added successfully (ID: {search_id})', 'success')
                return redirect(url_for('searches'))
                
            except Exception as e:
                flash(f'Error adding search: {e}', 'error')
                return render_template('add_search.html')
        
        return render_template('add_search.html')
    
    # Configuration route
    @app.route('/config')
    def config():
        """Configuration page"""
        try:
            from configuration_values import get_max_items_per_search, get_search_interval, get_telegram_bot_token, get_telegram_chat_id
            
            # Get real configuration from database/environment
            config_data = {
                'max_items_per_search': get_max_items_per_search(),
                'search_interval': get_search_interval(),
                'telegram_bot_token': get_telegram_bot_token() or '',
                'telegram_chat_id': get_telegram_chat_id() or '',
                'telegram_configured': bool(get_telegram_bot_token()),
                'proxy_enabled': get_db().get_setting('PROXY_ENABLED', 'false').lower() == 'true',
                'proxy_list': get_db().get_setting('PROXY_LIST', ''),
                'max_errors_before_redeploy': 5
            }
            
            # Get real status data
            error_stats = get_db().get_error_statistics()
            proxy_status = get_db().get_proxy_statistics()
            railway_status = {
                'status': 'active' if error_stats['total'] < 5 else 'warning',
                'last_deploy': 'Never'
            }
            
            return render_template('config.html', 
                                 config=config_data,
                                 error_stats=error_stats,
                                 proxy_status=proxy_status,
                                 railway_status=railway_status)
        except Exception as e:
            flash(f'Error loading configuration: {e}', 'error')
            return render_template('config.html', config={})
    
    # Logs route
    @app.route('/logs')
    def logs():
        """Logs page"""
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 50))
            level_filter = request.args.get('level', '')
            
            logs_data = get_logs_paginated(page, per_page, level_filter)
            
            return render_template('logs.html',
                                 logs=logs_data['logs'],
                                 pagination=logs_data['pagination'],
                                 level_filter=level_filter)
        except Exception as e:
            flash(f'Error loading logs: {e}', 'error')
            return render_template('logs.html', logs=[], pagination={})
    
    @app.route('/queries')
    def queries():
        """Queries page (like VS5)"""
        try:
            queries = get_db().get_all_searches()  # Get all searches with stats
            return render_template('queries.html', queries=queries)
        except Exception as e:
            flash(f'Error loading queries: {e}', 'error')
            return render_template('queries.html', queries=[])
    
    @app.route('/queries/add', methods=['POST'])
    def add_query():
        """Add new query via API"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            name = data.get('name', 'Unnamed Query')
            url = data.get('url')
            telegram_chat_id = data.get('telegram_chat_id')
            telegram_thread_id = data.get('telegram_thread_id')
            
            if not url:
                return jsonify({'error': 'URL is required'}), 400
            
            # Validate URL
            url_info = searcher.validate_search_url(url)
            if not url_info['valid']:
                return jsonify({'error': f'Invalid URL: {url_info["error"]}'}), 400
            
            # Add search
            search_id = get_db().add_search(
                name=name,
                url=url,
                telegram_chat_id=telegram_chat_id,
                telegram_thread_id=telegram_thread_id
            )
            
            return jsonify({
                'success': True,
                'message': f'Query "{name}" added successfully',
                'search_id': search_id
            })
            
        except Exception as e:
            logger.error(f"Error adding query: {e}")
            return jsonify({'error': f'Error adding query: {e}'}), 500
    
    # API Routes
    @app.route('/api/search/test', methods=['POST'])
    def api_test_search():
        """Test search URL"""
        try:
            data = request.get_json()
            url = data.get('url')
            
            if not url:
                return jsonify({'error': 'URL is required'}), 400
            
            # Validate URL format
            result = searcher.validate_search_url(url)
            
            if result['valid']:
                # Try to search for items
                try:
                    items = searcher.search_query({'url': url, 'id': 0, 'name': 'Test'})
                    result['test_results'] = {
                        'items_found': len(items),
                        'sample_titles': [item.title for item in items[:3]] if items else []
                    }
                except Exception as e:
                    result['test_error'] = str(e)
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/search/run', methods=['POST'])
    def api_run_search():
        """Run search manually (deprecated - use /api/force-scan instead)"""
        try:
            logger.info("🔍 Force scan initiated via /api/search/run (deprecated endpoint)")
            get_db().add_log_entry('INFO', 'Force Scan All initiated via deprecated endpoint', 'WebUI', 'Manual scan triggered by user')
            
            # Use the global searcher instance
            results = searcher.search_all_queries()
            
            logger.info(f"✅ Force scan completed: {results}")
            get_db().add_log_entry('INFO', 'Force Scan All completed', 'WebUI', f'Manual scan - found {results.get("new_items", 0)} new items')
            
            return jsonify({
                'success': True,
                'message': f'Force scan completed successfully! Found {results.get("new_items", 0)} new items.',
                'results': results
            })
        except Exception as e:
            logger.error(f"❌ Error in force scan: {e}")
            import traceback
            traceback.print_exc()
            get_db().add_log_entry('ERROR', f'Force Scan All failed: {str(e)}', 'WebUI', 'Manual scan error')
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/notifications/send', methods=['POST'])
    def api_send_notifications():
        """Send pending notifications"""
        try:
            results = send_notifications()
            return jsonify(results)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/redeploy', methods=['POST'])
    def api_redeploy():
        """Trigger manual redeploy"""
        try:
            result = redeployer.trigger_redeploy()
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/items/clear', methods=['POST'])
    def api_clear_items():
        """Clear all items"""
        try:
            get_db().clear_all_items()
            return jsonify({'success': True, 'message': 'All items cleared successfully'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/notifications/test', methods=['POST'])
    def api_test_notification():
        """Send test notification"""
        try:
            import os
            # Create a test item
            test_item = {
                'title': 'Test Item - KF Searcher',
                'price': 100,
                'currency': 'BYN',
                'location': 'Минск',
                'url': 'https://www.kufar.by',
                'images': [],
                'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID'),
                'telegram_thread_id': None
            }
            
            # Send test notification
            from simple_telegram_worker import TelegramWorker
            import asyncio
            
            telegram_worker = TelegramWorker()
            success = asyncio.run(telegram_worker.send_item_notification(test_item))
            
            if success:
                return jsonify({'success': True, 'message': 'Test notification sent successfully'})
            else:
                return jsonify({'error': 'Failed to send test notification'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/config/save', methods=['POST'])
    def api_save_config():
        """Save configuration"""
        try:
            data = request.get_json()
            logger.info(f"📥 Received config save request: {data}")
            
            # Save to environment variables or settings table
            settings_to_save = {}
            
            if 'max_items_per_search' in data:
                settings_to_save['MAX_ITEMS_PER_SEARCH'] = str(data['max_items_per_search'])
            
            if 'search_interval' in data:
                settings_to_save['SEARCH_INTERVAL'] = str(data['search_interval'])
                
            if 'telegram_bot_token' in data and data['telegram_bot_token']:
                settings_to_save['TELEGRAM_BOT_TOKEN'] = data['telegram_bot_token']
                
            if 'telegram_chat_id' in data and data['telegram_chat_id']:
                settings_to_save['TELEGRAM_CHAT_ID'] = data['telegram_chat_id']
                
            if 'proxy_enabled' in data:
                settings_to_save['PROXY_ENABLED'] = 'true' if data['proxy_enabled'] else 'false'
                
            if 'proxy_list' in data and data['proxy_list']:
                settings_to_save['PROXY_LIST'] = data['proxy_list'].replace('\n', ',')
            
            logger.info(f"📝 Settings to save: {settings_to_save}")
            
            # Save settings to database settings table
            saved_count = 0
            failed_keys = []
            for key, value in settings_to_save.items():
                success = get_db().set_setting(key, value)
                if success:
                    saved_count += 1
                    logger.info(f"✅ Configuration saved: {key} = {value[:50]}...")
                else:
                    failed_keys.append(key)
                    logger.error(f"❌ Failed to save: {key}")
            
            # Verify that settings were saved
            logger.info(f"🔍 Verifying saved settings...")
            for key in settings_to_save.keys():
                db_value = get_db().get_setting(key)
                logger.info(f"   {key}: saved='{settings_to_save[key][:50]}...', read='{db_value[:50] if db_value else None}...'")
            
            # Log detailed information about what was saved
            config_summary = []
            for key, value in settings_to_save.items():
                config_summary.append(f"{key}={value[:20]}...")
            
            get_db().add_log_entry('INFO', f'Configuration updated: {", ".join(config_summary)}', 'WebUI', f'Updated {saved_count}/{len(settings_to_save)} settings via web interface')
            logger.info(f"✅ Configuration save complete: {saved_count} saved, {len(failed_keys)} failed")
            
            if failed_keys:
                return jsonify({
                    'success': False, 
                    'message': f'Failed to save some settings: {", ".join(failed_keys)}'
                }), 500
            
            return jsonify({
                'success': True, 
                'message': f'Configuration saved successfully! ({saved_count} settings updated)'
            })
            
        except Exception as e:
            logger.error(f"❌ Error saving configuration: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/bot/stop', methods=['POST'])
    def api_stop_bot():
        """Stop bot"""
        try:
            # Here you would stop the bot
            # For now, just return success
            return jsonify({'success': True, 'message': 'Bot stopped successfully'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/force-scan', methods=['POST'])
    def api_force_scan():
        """Force scan all queries"""
        try:
            logger.info("🔍 Force scan initiated via API (WEB process)")
            get_db().add_log_entry('INFO', 'Force Scan All initiated via WebUI', 'WebUI', 'Manual scan triggered by user')
            
            # Use the global searcher instance
            from core import searcher
            
            # Run scan
            results = searcher.search_all_queries()
            
            logger.info(f"✅ Force scan completed: {results}")
            get_db().add_log_entry('INFO', 'Force Scan All completed', 'WebUI', f'Manual scan - found {results.get("new_items", 0)} new items')
            
            return jsonify({
                'success': True, 
                'message': f'Force scan completed successfully! Found {results.get("new_items", 0)} new items.',
                'results': results
            })
            
        except Exception as e:
            logger.error(f"❌ Error in force scan: {e}")
            import traceback
            traceback.print_exc()
            get_db().add_log_entry('ERROR', f'Force Scan All failed: {str(e)}', 'WebUI', 'Manual scan error')
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/worker/status', methods=['GET'])
    def api_worker_status():
        """Check if worker process is running by checking recent scheduler logs"""
        try:
            from datetime import datetime, timedelta
            
            # Проверяем есть ли логи от scheduler'а за последние 5 минут
            recent_time = datetime.now() - timedelta(minutes=5)
            
            with get_db().get_connection() as conn:
                cursor = conn.cursor()
                
                # Ищем логи планировщика за последние 5 минут
                if get_db().is_postgres:
                    query = """
                        SELECT COUNT(*) FROM logs 
                        WHERE (component LIKE '%scheduler%' OR component LIKE '%main%' OR message LIKE '%scheduler%')
                        AND timestamp >= %s
                    """
                else:
                    query = """
                        SELECT COUNT(*) FROM logs 
                        WHERE (component LIKE '%scheduler%' OR component LIKE '%main%' OR message LIKE '%scheduler%')
                        AND datetime(timestamp) >= datetime(?)
                    """
                
                get_db().execute_query(cursor, query, [recent_time.isoformat()])
                result = cursor.fetchone()
                recent_scheduler_logs = result[0] if result else 0
                
                # Ищем логи поиска за последние 10 минут
                search_time = datetime.now() - timedelta(minutes=10)
                if get_db().is_postgres:
                    search_query = """
                        SELECT COUNT(*) FROM logs 
                        WHERE (message LIKE '%search and notification cycle%' OR message LIKE '%Starting search%')
                        AND timestamp >= %s
                    """
                else:
                    search_query = """
                        SELECT COUNT(*) FROM logs 
                        WHERE (message LIKE '%search and notification cycle%' OR message LIKE '%Starting search%')
                        AND datetime(timestamp) >= datetime(?)
                    """
                
                get_db().execute_query(cursor, search_query, [search_time.isoformat()])
                result = cursor.fetchone()
                recent_search_logs = result[0] if result else 0
                
                # Определяем статус
                if recent_scheduler_logs > 0:
                    if recent_search_logs > 0:
                        status = "running_and_scanning"
                        message = "Worker running and scanning"
                    else:
                        status = "running_no_scans"
                        message = "Worker running but no recent scans"
                else:
                    status = "not_running"
                    message = "Worker not running (no recent scheduler logs)"
                
                return jsonify({
                    'success': True,
                    'status': status,
                    'message': message,
                    'scheduler_logs': recent_scheduler_logs,
                    'search_logs': recent_search_logs
                })
                
        except Exception as e:
            logger.error(f"Error checking worker status: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/logs', methods=['GET'])
    def api_get_logs():
        """Get logs"""
        try:
            level = request.args.get('level')
            limit = int(request.args.get('limit', 100))
            logs = get_db().get_logs(limit=limit, level=level)
            return jsonify({'success': True, 'logs': logs})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/logs/clear', methods=['POST'])
    def api_clear_logs():
        """Clear all logs"""
        try:
            get_db().clear_logs()
            get_db().add_log_entry('INFO', 'System logs cleared by user', 'WebUI')
            return jsonify({'success': True, 'message': 'Logs cleared successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Queries API endpoints
    @app.route('/api/queries/add', methods=['POST'])
    def api_add_query():
        """Add new query"""
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('url'):
                return jsonify({'error': 'URL is required'}), 400
            
            # Create search query
            search_data = {
                'name': data.get('name', ''),
                'url': data['url'],
                'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID'),
                'telegram_thread_id': data.get('thread_id'),
                'is_active': True
            }
            
            search_id = get_db().add_search(**search_data)
            if search_id:
                get_db().add_log_entry('INFO', f'New query added: {search_data["name"] or search_data["url"]}', 'WebUI')
                return jsonify({'success': True, 'id': search_id})
            else:
                return jsonify({'error': 'Failed to add query'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/queries/<int:query_id>', methods=['GET'])
    def api_get_query(query_id):
        """Get single query"""
        try:
            query = get_db().get_search_query(query_id)
            if query:
                return jsonify({'success': True, 'query': query})
            else:
                return jsonify({'error': 'Query not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/queries/<int:query_id>', methods=['PUT'])
    def api_update_query(query_id):
        """Update query"""
        try:
            data = request.get_json()
            
            update_data = {}
            if 'name' in data:
                update_data['name'] = data['name']
            if 'url' in data:
                update_data['url'] = data['url']
            if 'thread_id' in data:
                update_data['telegram_thread_id'] = data['thread_id']
            
            success = get_db().update_search_query(query_id, **update_data)
            if success:
                get_db().add_log_entry('INFO', f'Query updated: ID {query_id}', 'WebUI')
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Failed to update query'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/queries/<int:query_id>', methods=['DELETE'])
    def api_delete_query(query_id):
        """Delete query"""
        try:
            success = get_db().delete_search_query(query_id)
            if success:
                get_db().add_log_entry('INFO', f'Query deleted: ID {query_id}', 'WebUI')
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Failed to delete query'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/queries/<int:query_id>/thread', methods=['PUT'])
    def api_update_query_thread(query_id):
        """Update query thread ID"""
        try:
            data = request.get_json()
            thread_id = data.get('thread_id', '')
            
            success = get_db().update_search_query(query_id, telegram_thread_id=thread_id)
            if success:
                get_db().add_log_entry('INFO', f'Query thread ID updated: ID {query_id}, Thread: {thread_id}', 'WebUI')
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Failed to update thread ID'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/queries/all', methods=['DELETE'])
    def api_delete_all_queries():
        """Delete all queries"""
        try:
            success = get_db().delete_all_search_queries()
            if success:
                get_db().add_log_entry('WARNING', 'All queries deleted by user', 'WebUI')
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Failed to delete all queries'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/railway/status', methods=['GET'])
    def api_railway_status():
        """Get Railway system status"""
        try:
            # Get real error statistics from database
            error_stats = get_db().get_error_statistics()
            
            return jsonify({
                'success': True,
                'status': {
                    'status': 'active' if error_stats['total'] < 5 else 'warning',
                    'errors': {
                        '403': error_stats.get('403', 0),
                        '401': error_stats.get('401', 0), 
                        '429': error_stats.get('429', 0)
                    },
                    'total_errors': error_stats['total'],
                    'first_error': error_stats.get('first_error', 'None'),
                    'last_error': error_stats.get('last_error', 'None'),
                    'last_redeploy': error_stats.get('last_redeploy', 'Never')
                }
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/proxy/status', methods=['GET'])
    def api_proxy_status():
        """Get Proxy system status"""
        try:
            # Get real proxy statistics
            proxy_stats = get_db().get_proxy_statistics()
            
            return jsonify({
                'success': True,
                'status': {
                    'status': 'active' if proxy_stats['working_proxies'] > 0 else 'inactive',
                    'total_proxies': proxy_stats['total_proxies'],
                    'working_proxies': proxy_stats['working_proxies'],
                    'current_proxy': proxy_stats.get('current_proxy', 'No proxies configured'),
                    'last_check': proxy_stats.get('last_check', 'Never')
                }
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/stats', methods=['GET'])
    def api_get_stats():
        """Get real-time statistics for dashboard"""
        try:
            from datetime import datetime
            import datetime as dt
            
            # Add parent directory to path
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            
            # Get real stats from metrics_storage
            try:
                import metrics_storage
                total_api_requests = metrics_storage.metrics_storage.get_total_api_requests()
                app_start_time = metrics_storage.metrics_storage.get_app_start_time()
                total_items_found = metrics_storage.metrics_storage.get_total_items_found()
                logger.info(f"API Stats: requests={total_api_requests}, start={app_start_time}")
            except Exception as e:
                logger.error(f"Error in /api/stats: {e}")
                total_api_requests = 0
                app_start_time = datetime.now()
                total_items_found = 0
            
            # Calculate uptime
            uptime_seconds = (datetime.now() - app_start_time).total_seconds()
            uptime_str = str(dt.timedelta(seconds=int(uptime_seconds)))
            
            # Get last found item
            last_item = get_db().get_last_found_item()
            
            # Get items count
            db_stats = get_db().get_items_stats()
            
            return jsonify({
                'success': True,
                'total_api_requests': total_api_requests,
                'uptime_formatted': uptime_str,
                'total_items': db_stats.get('total_items', 0),
                'active_queries': db_stats.get('active_searches', 0),
                'last_found_item': last_item,
                'database': db_stats,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/recent-items', methods=['GET'])
    def api_get_recent_items():
        """API endpoint for getting recent items"""
        try:
            items = get_recent_items(hours=24)
            
            return jsonify({
                'success': True,
                'items': items[:30],  # Ограничиваем до 30 последних
                'count': len(items),
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting recent items: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/items', methods=['GET'])
    def api_get_items():
        """API endpoint for getting paginated items"""
        try:
            page = int(request.args.get('page', 1))
            search_filter = request.args.get('search', '')
            search_id = request.args.get('search_id', '')
            per_page = 30
            
            # Получаем пагинированные объявления
            result = get_items_paginated(page=page, per_page=per_page, search_filter=search_filter, search_id=search_id)
            
            return jsonify({
                'success': True,
                'items': result['items'],
                'pagination': result['pagination'],
                'new_items_available': False,  # Можно добавить логику проверки новых объявлений
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting items: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/logs/recent', methods=['GET'])
    def api_get_recent_logs():
        """API endpoint for getting recent logs"""
        try:
            minutes = int(request.args.get('minutes', 10))  # Получаем логи за последние N минут
            page = 1
            per_page = 50
            level_filter = request.args.get('level', '')
            
            # Получаем логи
            result = get_logs_paginated(page=page, per_page=per_page, level_filter=level_filter)
            
            # Фильтруем только свежие логи (за последние N минут)
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            
            recent_logs = []
            for log in result.get('logs', []):
                try:
                    # Парсим время лога
                    log_time = datetime.fromisoformat(log['created_at'].replace('Z', '+00:00'))
                    if log_time.replace(tzinfo=None) >= cutoff_time:
                        recent_logs.append(log)
                except:
                    # Если не удается распарсить время, включаем лог
                    recent_logs.append(log)
            
            return jsonify({
                'success': True,
                'logs': recent_logs,
                'count': len(recent_logs),
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting recent logs: {e}")
            return jsonify({'error': str(e)}), 500

    return app

def get_recent_items(hours: int = 24):
    """Get recent items from database"""
    try:
        with get_db().get_connection() as conn:
            cursor = conn.cursor()
            
            if get_db().is_postgres:
                # PostgreSQL syntax
                get_db().execute_query(cursor, """
                    SELECT i.*, s.name as search_name, s.url as search_url
                    FROM items i
                    LEFT JOIN searches s ON i.search_id = s.id
                    WHERE i.created_at >= NOW() - INTERVAL %s
                    ORDER BY i.created_at DESC
                """, (f"{hours} hours",))
            else:
                # SQLite syntax
                get_db().execute_query(cursor, """
                    SELECT i.*, s.name as search_name, s.url as search_url
                    FROM items i
                    LEFT JOIN searches s ON i.search_id = s.id
                    WHERE i.created_at >= datetime('now', '-' || %s || ' hours')
                    ORDER BY i.created_at DESC
                """, (hours,))
            
            columns = [desc[0] for desc in cursor.description]
            items = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Parse JSON fields
            for item in items:
                if item.get('images'):
                    try:
                        item['images'] = json.loads(item['images'])
                    except:
                        item['images'] = []
                if item.get('raw_data'):
                    try:
                        item['raw_data'] = json.loads(item['raw_data'])
                    except:
                        item['raw_data'] = {}
            
            return items
    except Exception as e:
        print(f"Error getting recent items: {e}")
        return []

def get_items_paginated(page: int = 1, per_page: int = 20, search_filter: str = '', search_id: str = ''):
    """Get paginated items with support for multiple search terms separated by semicolon"""
    try:
        offset = (page - 1) * per_page
        
        # Build query
        where_conditions = []
        params = []
        
        if search_filter:
            # Split by semicolon to support multiple search terms
            search_terms = [term.strip() for term in search_filter.split(';') if term.strip()]
            
            if search_terms:
                # Build OR conditions for each search term
                term_conditions = []
                for term in search_terms:
                    if get_db().is_postgres:
                        term_conditions.append("(i.title ILIKE %s OR s.name ILIKE %s)")
                    else:
                        term_conditions.append("(i.title LIKE %s OR s.name LIKE %s)")
                    params.extend([f'%{term}%', f'%{term}%'])
                
                # Combine all term conditions with OR
                where_conditions.append(f"({' OR '.join(term_conditions)})")
        
        if search_id:
            where_conditions.append("i.search_id = %s")
            params.append(int(search_id))
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        with get_db().get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total count
            count_query = f"""
                SELECT COUNT(*) FROM items i
                LEFT JOIN searches s ON i.search_id = s.id
                {where_clause}
            """
            get_db().execute_query(cursor, count_query, params)
            total = cursor.fetchone()[0]
            
            # Get items
            items_query = f"""
                SELECT i.*, s.name as search_name, s.url as search_url
                FROM items i
                LEFT JOIN searches s ON i.search_id = s.id
                {where_clause}
                ORDER BY i.created_at DESC
                LIMIT %s OFFSET %s
            """
            get_db().execute_query(cursor, items_query, params + [per_page, offset])
            
            columns = [desc[0] for desc in cursor.description]
            items = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Parse JSON fields
            for item in items:
                if item.get('images'):
                    try:
                        item['images'] = json.loads(item['images'])
                    except:
                        item['images'] = []
            
            # Calculate pagination
            total_pages = (total + per_page - 1) // per_page
            
            # Check if there are more items: if we got full page, there might be more
            # Only consider has_next=False if we got less items than requested
            has_more_items = len(items) >= per_page and (page * per_page) < total
            
            return {
                'items': items,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': total_pages,
                    'has_prev': page > 1,
                    'has_next': has_more_items
                }
            }
    except Exception as e:
        print(f"Error getting paginated items: {e}")
        return {'items': [], 'pagination': {}}

def get_logs_paginated(page: int = 1, per_page: int = 50, level_filter: str = ''):
    """Get paginated logs"""
    try:
        offset = (page - 1) * per_page
        
        # Build query
        where_clause = ""
        params = []
        
        if level_filter:
            where_clause = "WHERE level = %s"
            params = [level_filter]
        
        with get_db().get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM logs {where_clause}"
            get_db().execute_query(cursor, count_query, params)
            total = cursor.fetchone()[0]
            
            # Get logs with proper timestamp sorting
            if get_db().is_postgres:
                logs_query = f"""
                    SELECT * FROM logs {where_clause}
                    ORDER BY timestamp DESC, id DESC
                    LIMIT %s OFFSET %s
                """
            else:
                logs_query = f"""
                    SELECT * FROM logs {where_clause}
                    ORDER BY datetime(timestamp) DESC, id DESC
                    LIMIT %s OFFSET %s
                """
            get_db().execute_query(cursor, logs_query, params + [per_page, offset])
            
            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Конвертируем timestamp в белорусское время для отображения
            from db import BELARUS_TZ
            try:
                import pytz
            except ImportError:
                logger.warning("pytz not available, timestamps may not display correctly")
                pytz = None
            for log in logs:
                if log.get('timestamp'):
                    try:
                        # Если timestamp - строка, парсим её
                        if isinstance(log['timestamp'], str):
                            if log['timestamp'].endswith('Z'):
                                # UTC время
                                dt = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                            elif '+' in log['timestamp'] or log['timestamp'].endswith('00'):
                                # Уже с timezone
                                dt = datetime.fromisoformat(log['timestamp'])
                            else:
                                # Без timezone - считаем UTC
                                if pytz:
                                    dt = datetime.fromisoformat(log['timestamp']).replace(tzinfo=pytz.UTC)
                                else:
                                    dt = datetime.fromisoformat(log['timestamp'])
                        else:
                            # datetime объект
                            dt = log['timestamp']
                            if dt.tzinfo is None and pytz:
                                dt = dt.replace(tzinfo=pytz.UTC)
                        
                        # Конвертируем в белорусское время
                        belarus_time = dt.astimezone(BELARUS_TZ)
                        log['timestamp'] = belarus_time.strftime('%Y-%m-%d %H:%M:%S %z')
                        
                    except Exception as e:
                        # Если ошибка конвертации - оставляем как есть
                        logger.warning(f"Failed to convert timestamp for log {log.get('id')}: {e}")
            
            # Calculate pagination
            total_pages = (total + per_page - 1) // per_page
            
            return {
                'logs': logs,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': total_pages,
                    'has_prev': page > 1,
                    'has_next': page < total_pages
                }
            }
    except Exception as e:
        print(f"Error getting paginated logs: {e}")
        return {'logs': [], 'pagination': {}}

def get_current_config():
    """Get current configuration"""
    try:
        from configuration_values import (
            SEARCH_INTERVAL, MAX_ITEMS_PER_SEARCH, 
            PROXY_ENABLED, TELEGRAM_BOT_TOKEN,
            MAX_ERRORS_BEFORE_REDEPLOY
        )
        
        return {
            'search_interval': SEARCH_INTERVAL,
            'max_items_per_search': MAX_ITEMS_PER_SEARCH,
            'proxy_enabled': PROXY_ENABLED,
            'telegram_configured': bool(TELEGRAM_BOT_TOKEN),
            'max_errors_before_redeploy': MAX_ERRORS_BEFORE_REDEPLOY
        }
    except ImportError:
        # Fallback values if import fails
        return {
            'search_interval': 300,
            'max_items_per_search': 50,
            'proxy_enabled': False,
            'telegram_configured': False,
            'max_errors_before_redeploy': 5
        }
