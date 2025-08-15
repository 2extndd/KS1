"""
Flask web application for KF Searcher UI
Based on VS5 web interface, adapted for Kufar.by
"""

import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.exceptions import BadRequest

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import db
from core import searcher
from simple_telegram_worker import send_notifications
from railway_redeploy import redeployer
from configuration_values import SECRET_KEY

def create_app():
    """Create Flask application"""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    app.secret_key = SECRET_KEY
    
    # Dashboard route
    @app.route('/')
    def dashboard():
        """Main dashboard"""
        try:
            # Get statistics
            db_stats = db.get_items_stats()
            searcher_status = searcher.get_searcher_status()
            
            # Get recent items (last 24 hours)
            recent_items = get_recent_items(24)
            
            # Get active searches
            active_searches = db.get_active_searches()
            
            return render_template('dashboard.html',
                                 db_stats=db_stats,
                                 searcher_status=searcher_status,
                                 recent_items=recent_items[:10],  # Show last 10
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
            # Get current configuration
            config_data = get_current_config()
            return render_template('config.html', config=config_data)
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
    
    # API Routes
    @app.route('/api/search/test', methods=['POST'])
    def api_test_search():
        """Test search URL"""
        try:
            data = request.get_json()
            url = data.get('url')
            
            if not url:
                return jsonify({'error': 'URL is required'}), 400
            
            result = searcher.validate_search_url(url)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/search/run', methods=['POST'])
    def api_run_search():
        """Run search manually"""
        try:
            results = searcher.search_all_queries()
            return jsonify(results)
        except Exception as e:
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
    
    return app

def get_recent_items(hours: int = 24):
    """Get recent items from database"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.*, s.name as search_name
                FROM items i
                LEFT JOIN searches s ON i.search_id = s.id
                WHERE i.created_at >= NOW() - INTERVAL '%s hours'
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
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            # Get items
            items_query = f"""
                SELECT i.*, s.name as search_name
                FROM items i
                LEFT JOIN searches s ON i.search_id = s.id
                {where_clause}
                ORDER BY i.created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(items_query, params + [per_page, offset])
            
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
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            # Get logs
            logs_query = f"""
                SELECT * FROM logs {where_clause}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(logs_query, params + [per_page, offset])
            
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
    from ..configuration_values import (
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
