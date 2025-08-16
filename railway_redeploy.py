"""
Railway auto-redeploy functionality for KF Searcher
Based on VS5 railway redeploy system
"""

import requests
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from db import get_db
from configuration_values import (
    RAILWAY_TOKEN,
    RAILWAY_PROJECT_ID, 
    RAILWAY_SERVICE_ID,
    MAX_ERRORS_BEFORE_REDEPLOY,
    ERROR_CODES_FOR_REDEPLOY
)

logger = logging.getLogger(__name__)

class RailwayRedeployer:
    """Handles automatic redeployment on Railway when errors accumulate"""
    
    def __init__(self):
        self.railway_token = RAILWAY_TOKEN
        self.project_id = RAILWAY_PROJECT_ID
        self.service_id = RAILWAY_SERVICE_ID
        self.max_errors = MAX_ERRORS_BEFORE_REDEPLOY
        self.error_codes = ERROR_CODES_FOR_REDEPLOY
        
        self.base_url = "https://backboard.railway.app/graphql"
        self.headers = {
            "Authorization": f"Bearer {self.railway_token}",
            "Content-Type": "application/json"
        }
    
    def check_and_redeploy_if_needed(self) -> Dict[str, Any]:
        """Check error count and redeploy if threshold is reached"""
        try:
            if not self._is_configured():
                return {
                    'action': 'skipped',
                    'reason': 'Railway credentials not configured'
                }
            
            # Get recent errors from database
            recent_errors = self._get_recent_critical_errors()
            
            if len(recent_errors) >= self.max_errors:
                logger.warning(f"Found {len(recent_errors)} critical errors, triggering redeploy")
                
                # Attempt redeploy
                redeploy_result = self.trigger_redeploy()
                
                if redeploy_result['success']:
                    # Clear error tracking after successful redeploy
                    self._clear_error_tracking()
                    
                    return {
                        'action': 'redeployed',
                        'reason': f'Accumulated {len(recent_errors)} critical errors',
                        'deployment_id': redeploy_result.get('deployment_id'),
                        'errors_cleared': len(recent_errors)
                    }
                else:
                    return {
                        'action': 'redeploy_failed',
                        'reason': redeploy_result.get('error'),
                        'error_count': len(recent_errors)
                    }
            else:
                return {
                    'action': 'no_action',
                    'error_count': len(recent_errors),
                    'threshold': self.max_errors
                }
                
        except Exception as e:
            logger.error(f"Error in check_and_redeploy_if_needed: {e}")
            return {
                'action': 'error',
                'error': str(e)
            }
    
    def _get_recent_critical_errors(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get recent critical errors from database"""
        try:
            recent_errors = get_db().get_recent_errors(hours)
            
            # Filter for critical error codes
            critical_errors = [
                error for error in recent_errors 
                if error.get('error_code') in self.error_codes
            ]
            
            return critical_errors
            
        except Exception as e:
            logger.error(f"Error getting recent errors: {e}")
            return []
    
    def _is_configured(self) -> bool:
        """Check if Railway credentials are configured"""
        return all([
            self.railway_token,
            self.project_id,
            self.service_id
        ])
    
    def trigger_redeploy(self) -> Dict[str, Any]:
        """Trigger Railway redeploy via GraphQL API"""
        try:
            query = """
            mutation serviceRedeploy($serviceId: String!) {
                serviceRedeploy(serviceId: $serviceId) {
                    id
                    createdAt
                    status
                }
            }
            """
            
            variables = {
                "serviceId": self.service_id
            }
            
            payload = {
                "query": query,
                "variables": variables
            }
            
            response = requests.post(
                self.base_url,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'errors' in data:
                    error_msg = data['errors'][0]['message']
                    logger.error(f"GraphQL error: {error_msg}")
                    return {
                        'success': False,
                        'error': error_msg
                    }
                
                deployment = data.get('data', {}).get('serviceRedeploy', {})
                
                if deployment:
                    logger.info(f"Redeploy triggered successfully: {deployment['id']}")
                    return {
                        'success': True,
                        'deployment_id': deployment['id'],
                        'status': deployment.get('status'),
                        'created_at': deployment.get('createdAt')
                    }
                else:
                    return {
                        'success': False,
                        'error': 'No deployment data in response'
                    }
            else:
                logger.error(f"Railway API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return {
                'success': False,
                'error': f"Request failed: {e}"
            }
        except Exception as e:
            logger.error(f"Unexpected error in trigger_redeploy: {e}")
            return {
                'success': False,
                'error': f"Unexpected error: {e}"
            }
    
    def _clear_error_tracking(self):
        """Clear error tracking after successful redeploy"""
        try:
            with get_db().get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete recent error tracking entries
                if get_db().is_postgres:
                    # PostgreSQL syntax
                    get_db().execute_query(cursor, """
                        DELETE FROM error_tracking 
                        WHERE created_at >= NOW() - INTERVAL '2 hours'
                    """, ())
                else:
                    # SQLite syntax
                    get_db().execute_query(cursor, """
                        DELETE FROM error_tracking 
                        WHERE created_at >= datetime('now', '-2 hours')
                    """, ())
                
                conn.commit()
                logger.info("Error tracking cleared after redeploy")
                
        except Exception as e:
            logger.error(f"Error clearing error tracking: {e}")
    
    def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get status of a specific deployment"""
        try:
            query = """
            query deployment($id: String!) {
                deployment(id: $id) {
                    id
                    status
                    createdAt
                    updatedAt
                    url
                }
            }
            """
            
            variables = {
                "id": deployment_id
            }
            
            payload = {
                "query": query,
                "variables": variables
            }
            
            response = requests.post(
                self.base_url,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'errors' in data:
                    return {
                        'success': False,
                        'error': data['errors'][0]['message']
                    }
                
                deployment = data.get('data', {}).get('deployment', {})
                
                return {
                    'success': True,
                    'deployment': deployment
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error getting deployment status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the Railway service"""
        try:
            query = """
            query service($id: String!) {
                service(id: $id) {
                    id
                    name
                    createdAt
                    updatedAt
                    deployments(first: 5) {
                        edges {
                            node {
                                id
                                status
                                createdAt
                                url
                            }
                        }
                    }
                }
            }
            """
            
            variables = {
                "id": self.service_id
            }
            
            payload = {
                "query": query,
                "variables": variables
            }
            
            response = requests.post(
                self.base_url,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'errors' in data:
                    return {
                        'success': False,
                        'error': data['errors'][0]['message']
                    }
                
                service = data.get('data', {}).get('service', {})
                
                return {
                    'success': True,
                    'service': service
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error getting service info: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Global redeployer instance
redeployer = RailwayRedeployer()
