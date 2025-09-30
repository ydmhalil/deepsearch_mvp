"""
KOBİ Reporting System
Comprehensive business intelligence and reporting dashboard for small-medium businesses
"""

import sqlite3
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import seaborn as sns
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
import base64

class KOBIReportingSystem:
    def __init__(self, db_path='config/users.db', data_dir='data'):
        self.db_path = db_path
        self.data_dir = data_dir
        self.reports_dir = os.path.join(data_dir, 'reports')
        self.ensure_reports_directory()
        
    def ensure_reports_directory(self):
        """Ensure reports directory exists"""
        os.makedirs(self.reports_dir, exist_ok=True)
        
    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
        
    def generate_business_dashboard_data(self, company_id=None, date_range=30):
        """Generate comprehensive business dashboard data"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=date_range)
        
        dashboard = {
            'overview': self._get_business_overview(company_id, start_date, end_date),
            'search_analytics': self._get_search_analytics(company_id, start_date, end_date),
            'document_analytics': self._get_document_analytics(company_id, start_date, end_date),
            'user_productivity': self._get_user_productivity(company_id, start_date, end_date),
            'system_performance': self._get_system_performance(start_date, end_date),
            'trends': self._get_business_trends(company_id, start_date, end_date),
            'insights': self._generate_business_insights(company_id, start_date, end_date)
        }
        
        return dashboard
        
    def _get_business_overview(self, company_id, start_date, end_date):
        """Get high-level business overview metrics"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        overview = {}
        
        # Total searches
        cursor.execute('''
            SELECT COUNT(*) as total_searches,
                   AVG(response_time) as avg_response_time,
                   SUM(results_count) as total_results_shown
            FROM search_logs 
            WHERE timestamp BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        search_stats = cursor.fetchone()
        overview.update(dict(search_stats))
        
        # Active users
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) as active_users
            FROM search_logs 
            WHERE timestamp BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        overview['active_users'] = cursor.fetchone()['active_users']
        
        # Document statistics
        cursor.execute('''
            SELECT COUNT(*) as total_documents,
                   AVG(file_size) as avg_file_size,
                   SUM(file_size) as total_storage_used
            FROM documents
        ''')
        
        doc_stats = cursor.fetchone()
        overview.update(dict(doc_stats))
        
        # Search effectiveness
        cursor.execute('''
            SELECT 
                AVG(CASE WHEN results_count > 0 THEN 1.0 ELSE 0.0 END) as search_success_rate,
                AVG(results_count) as avg_results_per_search
            FROM search_logs 
            WHERE timestamp BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        effectiveness = cursor.fetchone()
        overview.update(dict(effectiveness))
        
        conn.close()
        return overview
        
    def _get_search_analytics(self, company_id, start_date, end_date):
        """Get detailed search analytics"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        analytics = {}
        
        # Daily search volume
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as searches
            FROM search_logs 
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''', (start_date, end_date))
        
        daily_searches = [dict(row) for row in cursor.fetchall()]
        analytics['daily_volume'] = daily_searches
        
        # Top search terms
        cursor.execute('''
            SELECT query, COUNT(*) as frequency,
                   AVG(results_count) as avg_results,
                   AVG(response_time) as avg_time
            FROM search_logs 
            WHERE timestamp BETWEEN ? AND ?
            AND query != ''
            GROUP BY query
            ORDER BY frequency DESC
            LIMIT 10
        ''', (start_date, end_date))
        
        analytics['top_queries'] = [dict(row) for row in cursor.fetchall()]
        
        # Search patterns by hour
        cursor.execute('''
            SELECT strftime('%H', timestamp) as hour, COUNT(*) as searches
            FROM search_logs 
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY strftime('%H', timestamp)
            ORDER BY hour
        ''', (start_date, end_date))
        
        analytics['hourly_patterns'] = [dict(row) for row in cursor.fetchall()]
        
        # Search success/failure rates
        cursor.execute('''
            SELECT 
                CASE WHEN results_count > 0 THEN 'Successful' ELSE 'No Results' END as result_type,
                COUNT(*) as count
            FROM search_logs 
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY result_type
        ''', (start_date, end_date))
        
        analytics['success_breakdown'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return analytics
        
    def _get_document_analytics(self, company_id, start_date, end_date):
        """Get document usage and management analytics"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        analytics = {}
        
        # Document types distribution
        cursor.execute('''
            SELECT file_type, COUNT(*) as count, SUM(file_size) as total_size
            FROM documents
            GROUP BY file_type
            ORDER BY count DESC
        ''')
        
        analytics['file_types'] = [dict(row) for row in cursor.fetchall()]
        
        # Document upload trends
        cursor.execute('''
            SELECT DATE(upload_date) as date, COUNT(*) as uploads, SUM(file_size) as daily_size
            FROM documents
            WHERE upload_date BETWEEN ? AND ?
            GROUP BY DATE(upload_date)
            ORDER BY date
        ''', (start_date, end_date))
        
        analytics['upload_trends'] = [dict(row) for row in cursor.fetchall()]
        
        # Most accessed documents (from search logs)
        cursor.execute('''
            SELECT 
                SUBSTR(query, 1, 50) as search_term,
                COUNT(*) as access_frequency
            FROM search_logs 
            WHERE timestamp BETWEEN ? AND ?
            AND results_count > 0
            GROUP BY search_term
            ORDER BY access_frequency DESC
            LIMIT 15
        ''', (start_date, end_date))
        
        analytics['popular_content'] = [dict(row) for row in cursor.fetchall()]
        
        # Storage utilization
        cursor.execute('''
            SELECT 
                SUM(file_size) as total_storage,
                COUNT(*) as total_files,
                AVG(file_size) as avg_file_size,
                MAX(file_size) as largest_file,
                MIN(file_size) as smallest_file
            FROM documents
        ''')
        
        analytics['storage_stats'] = dict(cursor.fetchone())
        
        conn.close()
        return analytics
        
    def _get_user_productivity(self, company_id, start_date, end_date):
        """Get user productivity metrics"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        productivity = {}
        
        # User activity levels
        cursor.execute('''
            SELECT 
                u.username,
                COUNT(sl.id) as total_searches,
                AVG(sl.response_time) as avg_search_time,
                COUNT(DISTINCT DATE(sl.timestamp)) as active_days
            FROM users u
            LEFT JOIN search_logs sl ON u.id = sl.user_id 
                AND sl.timestamp BETWEEN ? AND ?
            GROUP BY u.id, u.username
            ORDER BY total_searches DESC
        ''', (start_date, end_date))
        
        productivity['user_activity'] = [dict(row) for row in cursor.fetchall()]
        
        # Search effectiveness by user
        cursor.execute('''
            SELECT 
                u.username,
                AVG(CASE WHEN sl.results_count > 0 THEN 1.0 ELSE 0.0 END) as success_rate,
                AVG(sl.results_count) as avg_results
            FROM users u
            LEFT JOIN search_logs sl ON u.id = sl.user_id 
                AND sl.timestamp BETWEEN ? AND ?
            WHERE sl.id IS NOT NULL
            GROUP BY u.id, u.username
            HAVING COUNT(sl.id) >= 5
            ORDER BY success_rate DESC
        ''', (start_date, end_date))
        
        productivity['user_effectiveness'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return productivity
        
    def _get_system_performance(self, start_date, end_date):
        """Get system performance metrics"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        performance = {}
        
        # Response time trends
        cursor.execute('''
            SELECT DATE(timestamp) as date, 
                   AVG(response_time) as avg_response_time,
                   MAX(response_time) as max_response_time,
                   MIN(response_time) as min_response_time
            FROM search_logs 
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''', (start_date, end_date))
        
        performance['response_times'] = [dict(row) for row in cursor.fetchall()]
        
        # Peak usage times
        cursor.execute('''
            SELECT strftime('%H', timestamp) as hour,
                   COUNT(*) as search_count,
                   AVG(response_time) as avg_response_time
            FROM search_logs 
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY strftime('%H', timestamp)
            ORDER BY search_count DESC
        ''', (start_date, end_date))
        
        performance['peak_hours'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return performance
        
    def _get_business_trends(self, company_id, start_date, end_date):
        """Identify business trends and patterns"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        trends = {}
        
        # Weekly trends
        cursor.execute('''
            SELECT strftime('%W', timestamp) as week,
                   COUNT(*) as searches,
                   AVG(results_count) as avg_results
            FROM search_logs 
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY strftime('%W', timestamp)
            ORDER BY week
        ''', (start_date, end_date))
        
        trends['weekly_patterns'] = [dict(row) for row in cursor.fetchall()]
        
        # Content discovery trends (what types of content are being searched)
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN query LIKE '%pdf%' OR query LIKE '%belge%' THEN 'Belgeler'
                    WHEN query LIKE '%rapor%' OR query LIKE '%analiz%' THEN 'Raporlar'
                    WHEN query LIKE '%prosedür%' OR query LIKE '%süreç%' THEN 'Prosedürler'
                    WHEN query LIKE '%kişi%' OR query LIKE '%personel%' THEN 'İnsan Kaynakları'
                    ELSE 'Diğer'
                END as content_category,
                COUNT(*) as frequency
            FROM search_logs 
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY content_category
            ORDER BY frequency DESC
        ''', (start_date, end_date))
        
        trends['content_categories'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return trends
        
    def _generate_business_insights(self, company_id, start_date, end_date):
        """Generate actionable business insights"""
        insights = []
        
        # Get the analytics data for insight generation
        overview = self._get_business_overview(company_id, start_date, end_date)
        search_analytics = self._get_search_analytics(company_id, start_date, end_date)
        
        # Search effectiveness insights
        success_rate = overview.get('search_success_rate', 0.0) or 0.0
        if success_rate < 0.7:
            insights.append({
                'type': 'warning',
                'title': 'Düşük Arama Başarı Oranı',
                'description': f'Aramaların sadece %{success_rate*100:.1f}\'si sonuç buluyor. Belge indexleme ve arama optimizasyonu gerekli.',
                'recommendation': 'Belge etiketleme ve metadata geliştirme önerilir.'
            })
        elif success_rate > 0.9:
            insights.append({
                'type': 'success',
                'title': 'Mükemmel Arama Performansı',
                'description': f'Aramaların %{success_rate*100:.1f}\'si başarılı sonuçlar veriyor.',
                'recommendation': 'Mevcut sistem konfigürasyonu korunmalı.'
            })
            
        # User activity insights
        active_users = overview.get('active_users', 0)
        total_searches = overview.get('total_searches', 0)
        
        if active_users > 0 and total_searches/active_users > 50:
            insights.append({
                'type': 'info',
                'title': 'Yüksek Kullanıcı Aktivitesi',
                'description': f'Kullanıcı başına ortalama {total_searches/active_users:.1f} arama yapılıyor.',
                'recommendation': 'Sistem kullanımı yüksek, performans izlenmeli.'
            })
            
        # Response time insights
        avg_response = overview.get('avg_response_time', 0)
        if avg_response > 2.0:
            insights.append({
                'type': 'warning',
                'title': 'Yavaş Sistem Yanıtı',
                'description': f'Ortalama yanıt süresi {avg_response:.2f} saniye.',
                'recommendation': 'Index optimizasyonu ve performans iyileştirme gerekli.'
            })
            
        # Content trends
        top_queries = search_analytics.get('top_queries', [])
        if top_queries:
            most_searched = top_queries[0]
            insights.append({
                'type': 'info',
                'title': 'En Popüler Arama',
                'description': f'"{most_searched["query"]}" terimi {most_searched["frequency"]} kez arandı.',
                'recommendation': 'Bu konudaki belgelerin erişilebilirliği artırılabilir.'
            })
            
        return insights
        
    def generate_pdf_report(self, dashboard_data, report_title="KOBİ İş Raporu"):
        """Generate comprehensive PDF report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kobi_report_{timestamp}.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center
        )
        story.append(Paragraph(report_title, title_style))
        story.append(Paragraph(f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("YÖNETİCİ ÖZETİ", styles['Heading2']))
        overview = dashboard_data['overview']
        
        summary_data = [
            ['Metrik', 'Değer'],
            ['Toplam Arama Sayısı', f"{overview.get('total_searches', 0):,}"],
            ['Aktif Kullanıcı Sayısı', f"{overview.get('active_users', 0)}"],
            ['Ortalama Yanıt Süresi', f"{overview.get('avg_response_time', 0):.2f} saniye"],
            ['Arama Başarı Oranı', f"%{overview.get('search_success_rate', 0)*100:.1f}"],
            ['Toplam Belge Sayısı', f"{overview.get('total_documents', 0):,}"],
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Business Insights
        story.append(Paragraph("İŞ GÖRÜŞLARI", styles['Heading2']))
        insights = dashboard_data['insights']
        
        for insight in insights[:5]:  # Top 5 insights
            insight_style = styles['Normal']
            if insight['type'] == 'warning':
                insight_style = ParagraphStyle('Warning', parent=styles['Normal'], textColor=colors.red)
            elif insight['type'] == 'success':
                insight_style = ParagraphStyle('Success', parent=styles['Normal'], textColor=colors.green)
                
            story.append(Paragraph(f"<b>{insight['title']}</b>", styles['Heading4']))
            story.append(Paragraph(insight['description'], insight_style))
            story.append(Paragraph(f"<i>Öneri: {insight['recommendation']}</i>", styles['Italic']))
            story.append(Spacer(1, 10))
            
        story.append(PageBreak())
        
        # Search Analytics
        story.append(Paragraph("ARAMA ANALİTİKLERİ", styles['Heading2']))
        
        search_data = dashboard_data['search_analytics']
        
        # Top queries table
        story.append(Paragraph("En Çok Aranan Terimler", styles['Heading3']))
        
        query_table_data = [['Arama Terimi', 'Sıklık', 'Ort. Sonuç', 'Ort. Süre']]
        for query in search_data.get('top_queries', [])[:10]:
            query_table_data.append([
                query['query'][:30] + '...' if len(query['query']) > 30 else query['query'],
                str(query['frequency']),
                f"{query['avg_results']:.1f}",
                f"{query['avg_time']:.2f}s"
            ])
            
        query_table = Table(query_table_data)
        query_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(query_table)
        story.append(Spacer(1, 20))
        
        # User Productivity
        story.append(Paragraph("KULLANICI PRODÜKTİVİTESİ", styles['Heading3']))
        
        productivity = dashboard_data['user_productivity']
        user_table_data = [['Kullanıcı', 'Toplam Arama', 'Ort. Süre', 'Aktif Gün']]
        
        for user in productivity.get('user_activity', [])[:10]:
            user_table_data.append([
                user['username'],
                str(user['total_searches']),
                f"{user['avg_search_time']:.2f}s" if user['avg_search_time'] else 'N/A',
                str(user['active_days'])
            ])
            
        user_table = Table(user_table_data)
        user_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(user_table)
        
        # Build PDF
        try:
            doc.build(story)
            return filepath
        except Exception as e:
            print(f"PDF generation error: {e}")
            return None
            
    def generate_excel_report(self, dashboard_data, report_title="KOBİ Detay Raporu"):
        """Generate detailed Excel report with multiple sheets"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kobi_detail_{timestamp}.xlsx"
        filepath = os.path.join(self.reports_dir, filename)
        
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                
                # Overview sheet
                overview_df = pd.DataFrame([dashboard_data['overview']])
                overview_df.to_excel(writer, sheet_name='Genel Bakış', index=False)
                
                # Search analytics
                search_analytics = dashboard_data['search_analytics']
                
                # Top queries
                if search_analytics.get('top_queries'):
                    queries_df = pd.DataFrame(search_analytics['top_queries'])
                    queries_df.to_excel(writer, sheet_name='Popüler Aramalar', index=False)
                
                # Daily volume
                if search_analytics.get('daily_volume'):
                    daily_df = pd.DataFrame(search_analytics['daily_volume'])
                    daily_df.to_excel(writer, sheet_name='Günlük Arama Hacmi', index=False)
                
                # User productivity
                productivity = dashboard_data['user_productivity']
                if productivity.get('user_activity'):
                    users_df = pd.DataFrame(productivity['user_activity'])
                    users_df.to_excel(writer, sheet_name='Kullanıcı Aktivitesi', index=False)
                    
                # Document analytics
                doc_analytics = dashboard_data['document_analytics']
                if doc_analytics.get('file_types'):
                    files_df = pd.DataFrame(doc_analytics['file_types'])
                    files_df.to_excel(writer, sheet_name='Dosya Türleri', index=False)
                
                # Insights
                insights_df = pd.DataFrame(dashboard_data['insights'])
                insights_df.to_excel(writer, sheet_name='İş Görüşleri', index=False)
                
            return filepath
            
        except Exception as e:
            print(f"Excel generation error: {e}")
            return None
            
    def create_dashboard_charts(self, dashboard_data):
        """Create visualization charts for dashboard"""
        charts = {}
        
        try:
            # Set Turkish font for matplotlib
            plt.rcParams['font.family'] = ['DejaVu Sans']
            
            # 1. Daily search volume chart
            search_analytics = dashboard_data['search_analytics']
            daily_data = search_analytics.get('daily_volume', [])
            
            if daily_data:
                dates = [item['date'] for item in daily_data]
                searches = [item['searches'] for item in daily_data]
                
                plt.figure(figsize=(10, 6))
                plt.plot(dates, searches, marker='o', linewidth=2, markersize=6)
                plt.title('Günlük Arama Hacmi', fontsize=14, fontweight='bold')
                plt.xlabel('Tarih')
                plt.ylabel('Arama Sayısı')
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # Save as base64
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                buffer.seek(0)
                charts['daily_searches'] = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                
            # 2. Top queries pie chart
            top_queries = search_analytics.get('top_queries', [])
            if top_queries:
                labels = [q['query'][:20] + '...' if len(q['query']) > 20 else q['query'] for q in top_queries[:8]]
                sizes = [q['frequency'] for q in top_queries[:8]]
                
                plt.figure(figsize=(10, 8))
                plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                plt.title('En Popüler Arama Terimleri', fontsize=14, fontweight='bold')
                plt.axis('equal')
                
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                buffer.seek(0)
                charts['top_queries'] = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                
            # 3. Hourly search patterns
            hourly_data = search_analytics.get('hourly_patterns', [])
            if hourly_data:
                hours = [int(item['hour']) for item in hourly_data]
                searches = [item['searches'] for item in hourly_data]
                
                plt.figure(figsize=(12, 6))
                plt.bar(hours, searches, color='skyblue', alpha=0.8)
                plt.title('Saatlik Arama Dağılımı', fontsize=14, fontweight='bold')
                plt.xlabel('Saat')
                plt.ylabel('Arama Sayısı')
                plt.xticks(range(0, 24))
                plt.grid(axis='y', alpha=0.3)
                
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                buffer.seek(0)
                charts['hourly_patterns'] = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                
            # 4. File types distribution
            doc_analytics = dashboard_data['document_analytics']
            file_types = doc_analytics.get('file_types', [])
            if file_types:
                types = [ft['file_type'] for ft in file_types]
                counts = [ft['count'] for ft in file_types]
                
                plt.figure(figsize=(10, 6))
                plt.bar(types, counts, color=['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC'])
                plt.title('Dosya Türleri Dağılımı', fontsize=14, fontweight='bold')
                plt.xlabel('Dosya Türü')
                plt.ylabel('Dosya Sayısı')
                plt.xticks(rotation=45)
                
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                buffer.seek(0)
                charts['file_types'] = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                
        except Exception as e:
            print(f"Chart generation error: {e}")
            
        return charts

# Global reporting system instance
kobi_reporting = KOBIReportingSystem()