"""
Document Classification Manager
Handles professional categorization and security-level based access control
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import re
import json

class DocumentClassificationManager:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), 'config', 'users.db')
    
    def get_db_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ================== PROFESSIONAL CATEGORIES ==================
    
    def get_professional_categories(self) -> List[Dict]:
        """Get all active professional categories"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, description, color_code, icon, created_at, is_active
            FROM professional_categories 
            WHERE is_active = 1
            ORDER BY name
        ''')
        
        categories = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return categories
    
    def create_professional_category(self, name: str, description: str = "", 
                                   color_code: str = "#667eea", icon: str = "folder", 
                                   created_by: int = 1) -> int:
        """Create a new professional category"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO professional_categories (name, description, color_code, icon, created_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, description, color_code, icon, created_by))
        
        category_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return category_id
    
    # ================== SECURITY LEVELS ==================
    
    def get_security_levels(self) -> List[Dict]:
        """Get all active security levels"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, level_number, description, color_code, requirements, is_active
            FROM security_levels 
            WHERE is_active = 1
            ORDER BY level_number
        ''')
        
        levels = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return levels
    
    def create_security_level(self, name: str, level_number: int, description: str = "",
                            color_code: str = "#10b981", requirements: str = "") -> int:
        """Create a new security level"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO security_levels (name, level_number, description, color_code, requirements)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, level_number, description, color_code, requirements))
        
        level_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return level_id
    
    # ================== USER PERMISSIONS ==================
    
    def get_user_permissions(self, user_id: int) -> Dict:
        """Get user's category and security level permissions"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Get category permissions
        cursor.execute('''
            SELECT 
                up.id, up.permission_type, up.granted_at, up.expires_at,
                pc.id as category_id, pc.name as category_name, pc.color_code, pc.icon
            FROM user_permissions up
            JOIN professional_categories pc ON up.category_id = pc.id
            WHERE up.user_id = ? AND up.is_active = 1 AND up.category_id IS NOT NULL
            ORDER BY pc.name
        ''', (user_id,))
        
        category_permissions = [dict(row) for row in cursor.fetchall()]
        
        # Get security level permissions
        cursor.execute('''
            SELECT 
                up.id, up.permission_type, up.granted_at, up.expires_at,
                sl.id as security_level_id, sl.name as level_name, sl.level_number, sl.color_code
            FROM user_permissions up
            JOIN security_levels sl ON up.security_level_id = sl.id
            WHERE up.user_id = ? AND up.is_active = 1 AND up.security_level_id IS NOT NULL
            ORDER BY sl.level_number
        ''', (user_id,))
        
        security_permissions = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'categories': category_permissions,
            'security_levels': security_permissions,
            'max_security_level': max([p['level_number'] for p in security_permissions], default=0)
        }
    
    def grant_user_permission(self, user_id: int, category_id: int = None, 
                            security_level_id: int = None, permission_type: str = "read",
                            granted_by: int = 1, expires_at: str = None, notes: str = "") -> int:
        """Grant permission to user for category or security level"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_permissions 
            (user_id, category_id, security_level_id, permission_type, granted_by, expires_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, category_id, security_level_id, permission_type, granted_by, expires_at, notes))
        
        permission_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return permission_id
    
    def revoke_user_permission(self, permission_id: int) -> bool:
        """Revoke a user permission"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_permissions 
            SET is_active = 0 
            WHERE id = ?
        ''', (permission_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    # ================== DOCUMENT CLASSIFICATION ==================
    
    def classify_document(self, document_id: int, category_id: int, security_level_id: int,
                         classified_by: int, method: str = "manual", confidence: float = 1.0,
                         notes: str = "") -> int:
        """Classify a document with category and security level"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO document_classifications 
            (document_id, category_id, security_level_id, classification_method, 
             confidence_score, classified_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (document_id, category_id, security_level_id, method, confidence, classified_by, notes))
        
        classification_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return classification_id
    
    def get_document_classification(self, document_id: int) -> Optional[Dict]:
        """Get document's classification"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                dc.*, 
                pc.name as category_name, pc.color_code as category_color, pc.icon as category_icon,
                sl.name as security_level_name, sl.level_number, sl.color_code as security_color
            FROM document_classifications dc
            JOIN professional_categories pc ON dc.category_id = pc.id
            JOIN security_levels sl ON dc.security_level_id = sl.id
            WHERE dc.document_id = ?
        ''', (document_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None
    
    def auto_classify_document(self, document_content: str, document_id: int, 
                             classified_by: int) -> Optional[Dict]:
        """Automatically classify document based on content and rules"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Get classification rules
        cursor.execute('''
            SELECT cr.*, pc.name as category_name, sl.name as security_level_name
            FROM classification_rules cr
            JOIN professional_categories pc ON cr.category_id = pc.id
            JOIN security_levels sl ON cr.security_level_id = sl.id
            WHERE cr.is_active = 1
            ORDER BY cr.confidence_threshold DESC
        ''')
        
        rules = cursor.fetchall()
        content_lower = document_content.lower()
        
        best_match = None
        best_score = 0.0
        
        for rule in rules:
            keywords = rule['keywords'].split(',')
            matches = 0
            total_keywords = len(keywords)
            
            for keyword in keywords:
                keyword = keyword.strip().lower()
                if keyword in content_lower:
                    matches += 1
            
            score = matches / total_keywords if total_keywords > 0 else 0
            
            if score >= rule['confidence_threshold'] and score > best_score:
                best_score = score
                best_match = {
                    'rule_id': rule['id'],
                    'category_id': rule['category_id'],
                    'security_level_id': rule['security_level_id'],
                    'confidence': score,
                    'category_name': rule['category_name'],
                    'security_level_name': rule['security_level_name'],
                    'matched_keywords': [kw.strip() for kw in keywords if kw.strip().lower() in content_lower]
                }
        
        conn.close()
        
        # If auto-classification found a match, save it
        if best_match and best_match['confidence'] > 0.5:
            classification_id = self.classify_document(
                document_id=document_id,
                category_id=best_match['category_id'],
                security_level_id=best_match['security_level_id'],
                classified_by=classified_by,
                method="automatic",
                confidence=best_match['confidence'],
                notes=f"Auto-classified based on keywords: {', '.join(best_match['matched_keywords'])}"
            )
            best_match['classification_id'] = classification_id
        
        return best_match
    
    # ================== ACCESS CONTROL ==================
    
    def check_document_access(self, user_id: int, document_id: int) -> Dict:
        """Check if user has access to a document"""
        # Get user permissions
        user_perms = self.get_user_permissions(user_id)
        
        # Get document classification
        doc_classification = self.get_document_classification(document_id)
        
        if not doc_classification:
            # Unclassified documents default to "Açık" level
            return {
                'access_granted': True,
                'reason': 'Document not classified (default open access)',
                'classification': None
            }
        
        # Check category access
        user_categories = [cat['category_id'] for cat in user_perms['categories']]
        category_access = doc_classification['category_id'] in user_categories
        
        # Check security level access
        user_max_level = user_perms['max_security_level']
        security_access = user_max_level >= doc_classification['level_number']
        
        access_granted = category_access and security_access
        
        reason = ""
        if not category_access:
            reason = f"Category access denied: {doc_classification['category_name']}"
        elif not security_access:
            reason = f"Security level insufficient: requires {doc_classification['security_level_name']} (level {doc_classification['level_number']})"
        else:
            reason = "Access granted"
        
        return {
            'access_granted': access_granted,
            'reason': reason,
            'classification': doc_classification,
            'user_permissions': user_perms
        }
    
    def log_document_access(self, user_id: int, document_id: int, action: str, 
                          access_granted: bool, reason: str = "", ip_address: str = "",
                          user_agent: str = "", session_id: str = "") -> int:
        """Log document access attempt"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO access_audit_log 
            (user_id, document_id, action, access_granted, reason, ip_address, user_agent, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, document_id, action, access_granted, reason, ip_address, user_agent, session_id))
        
        log_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return log_id
    
    # ================== FILTERING FOR SEARCH ==================
    
    def filter_search_results(self, user_id: int, documents: List[Dict]) -> List[Dict]:
        """Filter search results based on user permissions"""
        filtered_results = []
        
        for doc in documents:
            # Extract document ID from file path or metadata
            document_id = doc.get('document_id', None)
            
            if document_id:
                access_check = self.check_document_access(user_id, document_id)
                if access_check['access_granted']:
                    # Add classification info to result
                    doc['classification'] = access_check['classification']
                    filtered_results.append(doc)
                else:
                    # Log access denial
                    self.log_document_access(
                        user_id=user_id,
                        document_id=document_id,
                        action="search_result_filtered",
                        access_granted=False,
                        reason=access_check['reason']
                    )
            else:
                # If no document ID, allow access (legacy documents)
                filtered_results.append(doc)
        
        return filtered_results
    
    # ================== STATISTICS ==================
    
    def get_classification_statistics(self) -> Dict:
        """Get classification system statistics"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Count documents by category
        cursor.execute('''
            SELECT pc.name, pc.color_code, COUNT(dc.id) as count
            FROM professional_categories pc
            LEFT JOIN document_classifications dc ON pc.id = dc.category_id
            WHERE pc.is_active = 1
            GROUP BY pc.id, pc.name, pc.color_code
            ORDER BY count DESC
        ''')
        categories_stats = [dict(row) for row in cursor.fetchall()]
        
        # Count documents by security level
        cursor.execute('''
            SELECT sl.name, sl.color_code, sl.level_number, COUNT(dc.id) as count
            FROM security_levels sl
            LEFT JOIN document_classifications dc ON sl.id = dc.security_level_id
            WHERE sl.is_active = 1
            GROUP BY sl.id, sl.name, sl.color_code, sl.level_number
            ORDER BY sl.level_number
        ''')
        security_stats = [dict(row) for row in cursor.fetchall()]
        
        # Total classified documents
        cursor.execute('SELECT COUNT(*) as total FROM document_classifications')
        total_classified = cursor.fetchone()['total']
        
        # Total documents
        cursor.execute('SELECT COUNT(*) as total FROM documents')
        total_documents = cursor.fetchone()['total']
        
        # Recent access attempts
        cursor.execute('''
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN access_granted = 1 THEN 1 ELSE 0 END) as granted,
                   SUM(CASE WHEN access_granted = 0 THEN 1 ELSE 0 END) as denied
            FROM access_audit_log 
            WHERE datetime(timestamp) >= datetime('now', '-24 hours')
        ''')
        access_stats = dict(cursor.fetchone())
        
        conn.close()
        
        return {
            'categories': categories_stats,
            'security_levels': security_stats,
            'total_classified': total_classified,
            'total_documents': total_documents,
            'classification_rate': (total_classified / total_documents * 100) if total_documents > 0 else 0,
            'access_stats_24h': access_stats
        }

# Global instance
classification_manager = DocumentClassificationManager()