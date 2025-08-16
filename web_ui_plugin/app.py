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

from db import db
from core import searcher
from simple_telegram_worker import send_notifications
from railway_redeploy import redeployer
from configuration_values import SECRET_KEY

def extract_size_from_item_data(item):
    """Extract size information from item data for WebUI"""
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
    
    return size.strip() if size else ""

def format_price_with_size(item):
    """Format price with size in format '75 BYN - 48 (M)'"""
    price = item.get('price', 0)
    currency = item.get('currency', 'BYN')
    
    # Format price
    price_text = f"{price:,} {currency}".replace(',', ' ') if price > 0 else "Цена не указана"
    
    # Extract size
    size = extract_size_from_item_data(item)
    
    # Combine price and size
    if size:
        return f"{price_text} - {size}"
    else:
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
            db_stats = db.get_items_stats()
            
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
            last_item = db.get_last_found_item()
            
            searcher_status = {
                'total_api_requests': total_api_requests,
                'uptime': uptime_str,
                'last_found_item': last_item,
                'is_running': True
            }
            
            # Get recent items (last 24 hours)
            recent_items = get_recent_items(24)
            
            # Get active searches
            active_searches = db.get_active_searches()
            
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
            per_page = int(request.args.get('per_page', 20))
            search_filter = request.args.get('search', '')
            
            items_data = get_items_paginated(page, per_page, search_filter)
            
            return render_template('items.html',
                                 items=items_data['items'],
                                 pagination=items_data['pagination'],
                                 search_filter=search_filter)
        except Exception as e:
            flash(f'Error loading items: {e}', 'error')
            return render_template('items.html', items=[], pagination={})
    
    # Searches/Queries route
    @app.route('/searches')
    def searches():
        """Searches management page"""
        try:
            searches = db.get_active_searches()
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
                search_id = db.add_search(
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
            from configuration_values import get_max_items_per_search, get_search_interval, get_telegram_bot_token
            
            # Get real configuration from database/environment
            config_data = {
                'max_items_per_search': get_max_items_per_search(),
                'search_interval': get_search_interval(),
                'telegram_configured': bool(get_telegram_bot_token()),
                'proxy_enabled': db.get_setting('PROXY_ENABLED', 'false').lower() == 'true',
                'max_errors_before_redeploy': 5
            }
            
            # Get real status data
            error_stats = db.get_error_statistics()
            proxy_status = db.get_proxy_statistics()
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
            queries = db.get_all_searches()  # Get all searches with stats
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
            search_id = db.add_search(
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
        """Run search manually"""
        try:
            print(f"🔍 Force Scan All triggered at {datetime.now()}")
            db.add_log_entry('INFO', 'Force Scan All triggered manually', 'Web UI', 'User requested manual search')
            
            results = searcher.search_all_queries()
            
            print(f"🔍 Force Scan completed: {results}")
            db.add_log_entry('INFO', f'Force Scan completed: {results}', 'Web UI', 'Manual search results')
            
            return jsonify(results)
        except Exception as e:
            error_msg = f"Error in Force Scan: {e}"
            print(f"❌ {error_msg}")
            db.add_log_entry('ERROR', error_msg, 'Web UI', 'Force scan error')
            return jsonify({'error': str(e)}), 500
    
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
    
    @app.route('/api/stats')
    def api_stats():
        """Get current statistics"""
        try:
            return jsonify({
                'database': db.get_items_stats(),
                'searcher': searcher.get_searcher_status(),
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/items/clear', methods=['POST'])
    def api_clear_items():
        """Clear all items"""
        try:
            db.clear_all_items()
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
            
            # Save settings to database settings table
            for key, value in settings_to_save.items():
                db.set_setting(key, value)
            
            db.add_log_entry('INFO', f'Configuration updated: {len(settings_to_save)} settings changed', 'WebUI', 'Configuration save operation')
            
            return jsonify({'success': True, 'message': 'Configuration saved successfully'})
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
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
            logger.info("Force scan initiated via API")
            
            # Import SearchCore from core module
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from core import KufarSearcher
            
            # Initialize KufarSearcher and run scan
            search_core = KufarSearcher()
            results = search_core.search_all_queries()
            
            logger.info(f"Force scan completed: {results}")
            db.add_log_entry('INFO', 'Force Scan All initiated via WebUI', 'WebUI', f'Manual scan triggered - found {results.get("new_items", 0)} new items')
            
            return jsonify({
                'success': True, 
                'message': f'Force scan completed successfully! Found {results.get("new_items", 0)} new items.',
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Error in force scan: {e}")
            import traceback
            traceback.print_exc()
            db.add_log_entry('ERROR', f'Force Scan All failed: {str(e)}', 'WebUI', 'Manual scan error')
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
            logs = db.get_logs(limit=limit, level=level)
            return jsonify({'success': True, 'logs': logs})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/logs/clear', methods=['POST'])
    def api_clear_logs():
        """Clear all logs"""
        try:
            db.clear_logs()
            db.add_log_entry('INFO', 'System logs cleared by user', 'WebUI')
            return jsonify({'success': True, 'message': 'Logs cleared successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/logs/recent', methods=['GET'])
    def api_get_recent_logs():
        """Get recent logs"""
        try:
            minutes = int(request.args.get('minutes', 5))
            logs = db.get_recent_logs(minutes=minutes)
            return jsonify({'success': True, 'logs': logs})
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
            
            search_id = db.add_search(**search_data)
            if search_id:
                db.add_log_entry('INFO', f'New query added: {search_data["name"] or search_data["url"]}', 'WebUI')
                return jsonify({'success': True, 'id': search_id})
            else:
                return jsonify({'error': 'Failed to add query'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/queries/<int:query_id>', methods=['GET'])
    def api_get_query(query_id):
        """Get single query"""
        try:
            query = db.get_search_query(query_id)
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
            
            success = db.update_search_query(query_id, **update_data)
            if success:
                db.add_log_entry('INFO', f'Query updated: ID {query_id}', 'WebUI')
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Failed to update query'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/queries/<int:query_id>', methods=['DELETE'])
    def api_delete_query(query_id):
        """Delete query"""
        try:
            success = db.delete_search_query(query_id)
            if success:
                db.add_log_entry('INFO', f'Query deleted: ID {query_id}', 'WebUI')
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
            
            success = db.update_search_query(query_id, telegram_thread_id=thread_id)
            if success:
                db.add_log_entry('INFO', f'Query thread ID updated: ID {query_id}, Thread: {thread_id}', 'WebUI')
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Failed to update thread ID'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/queries/all', methods=['DELETE'])
    def api_delete_all_queries():
        """Delete all queries"""
        try:
            success = db.delete_all_search_queries()
            if success:
                db.add_log_entry('WARNING', 'All queries deleted by user', 'WebUI')
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
            error_stats = db.get_error_statistics()
            
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
            proxy_stats = db.get_proxy_statistics()
            
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
            last_item = db.get_last_found_item()
            
            # Get items count
            db_stats = db.get_items_stats()
            
            return jsonify({
                'success': True,
                'stats': {
                    'total_api_requests': total_api_requests,
                    'uptime': uptime_str,
                    'total_items': db_stats.get('total_items', 0),
                    'active_queries': db_stats.get('active_searches', 0),
                    'last_found_item': last_item
                }
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
            per_page = 20
            
            # Получаем пагинированные объявления
            result = get_items_paginated(page=page, per_page=per_page, search_filter=search_filter)
            
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

    return app

def get_recent_items(hours: int = 24):
    """Get recent items from database"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            if db.is_postgres:
                # PostgreSQL syntax
                db.execute_query(cursor, """
                    SELECT i.*, s.name as search_name, s.url as search_url
                    FROM items i
                    LEFT JOIN searches s ON i.search_id = s.id
                    WHERE i.created_at >= NOW() - INTERVAL %s
                    ORDER BY i.created_at DESC
                """, (f"{hours} hours",))
            else:
                # SQLite syntax
                db.execute_query(cursor, """
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

def get_items_paginated(page: int = 1, per_page: int = 20, search_filter: str = ''):
    """Get paginated items"""
    try:
        offset = (page - 1) * per_page
        
        # Build query
        where_clause = ""
        params = []
        
        if search_filter:
            where_clause = "WHERE i.title ILIKE %s OR s.name ILIKE %s"
            params = [f'%{search_filter}%', f'%{search_filter}%']
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total count
            count_query = f"""
                SELECT COUNT(*) FROM items i
                LEFT JOIN searches s ON i.search_id = s.id
                {where_clause}
            """
            db.execute_query(cursor, count_query, params)
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
            db.execute_query(cursor, items_query, params + [per_page, offset])
            
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
            
            return {
                'items': items,
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
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM logs {where_clause}"
            db.execute_query(cursor, count_query, params)
            total = cursor.fetchone()[0]
            
            # Get logs
            logs_query = f"""
                SELECT * FROM logs {where_clause}
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
            """
            db.execute_query(cursor, logs_query, params + [per_page, offset])
            
            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
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
