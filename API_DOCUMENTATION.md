# DeepSearch MVP - API Documentation

## API Overview

DeepSearch MVP provides a RESTful API for document search, user management, and system administration. All API endpoints require authentication unless specified otherwise.

## Base URL

```
http://your-domain.com/api/v1
```

## Authentication

DeepSearch uses session-based authentication. After login, include the session cookie in subsequent requests.

### Login

```http
POST /login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "user@example.com",
    "role": "user",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "message": "Login successful"
}
```

### Logout

```http
POST /logout
```

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

## Search API

### Basic Search

Search through indexed documents using natural language queries.

```http
POST /search
Content-Type: application/json
Authorization: Required

{
  "query": "artificial intelligence machine learning",
  "top_k": 10
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "rank": 1,
      "similarity": 0.89,
      "file_path": "documents/ai_research.pdf",
      "chunk_text": "Artificial intelligence and machine learning technologies...",
      "start_pos": 1024,
      "end_pos": 1524,
      "chunk_id": "chunk_123",
      "metadata": {
        "file_type": "pdf",
        "upload_date": "2024-01-15T10:30:00Z",
        "file_size": 2048576
      }
    }
  ],
  "total_results": 25,
  "search_time_ms": 150,
  "query_id": "search_789"
}
```

### Advanced Search with Filters

```http
POST /search/advanced
Content-Type: application/json
Authorization: Required

{
  "query": "financial report analysis",
  "filters": {
    "file_types": ["pdf", "xlsx"],
    "date_from": "2024-01-01",
    "date_to": "2024-12-31",
    "min_size": 1024,
    "max_size": 10485760,
    "user_files_only": true
  },
  "sort_by": "relevance",
  "top_k": 20
}
```

**Response:**
```json
{
  "success": true,
  "results": [...],
  "filters_applied": {
    "file_types": ["pdf", "xlsx"],
    "date_range": "2024-01-01 to 2024-12-31",
    "size_range": "1KB to 10MB"
  },
  "total_results": 15,
  "filtered_results": 8
}
```

### Search History

```http
GET /search/history?page=1&per_page=20
Authorization: Required
```

**Response:**
```json
{
  "success": true,
  "searches": [
    {
      "id": 123,
      "query": "artificial intelligence",
      "timestamp": "2024-01-15T14:30:00Z",
      "results_count": 25,
      "search_time_ms": 150
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 5,
    "total_items": 98
  }
}
```

## Document Management API

### Upload Document

```http
POST /documents/upload
Content-Type: multipart/form-data
Authorization: Required

Form data:
- file: [binary file data]
- auto_index: true
- category: "business_report"
```

**Response:**
```json
{
  "success": true,
  "document": {
    "id": 456,
    "filename": "quarterly_report.pdf",
    "file_path": "uploads/user_123/quarterly_report.pdf",
    "file_size": 2048576,
    "file_type": "pdf",
    "upload_date": "2024-01-15T15:45:00Z",
    "is_processed": false,
    "processing_status": "queued"
  },
  "message": "Document uploaded successfully"
}
```

### List Documents

```http
GET /documents?page=1&per_page=20&file_type=pdf&sort=upload_date&order=desc
Authorization: Required
```

**Response:**
```json
{
  "success": true,
  "documents": [
    {
      "id": 456,
      "filename": "quarterly_report.pdf",
      "file_size": 2048576,
      "file_type": "pdf",
      "upload_date": "2024-01-15T15:45:00Z",
      "is_processed": true,
      "processing_status": "completed",
      "insights": {
        "business_category": "financial",
        "sentiment_score": 0.75,
        "key_topics": ["revenue", "growth", "market analysis"]
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 3,
    "total_items": 58
  }
}
```

### Document Details

```http
GET /documents/456
Authorization: Required
```

**Response:**
```json
{
  "success": true,
  "document": {
    "id": 456,
    "filename": "quarterly_report.pdf",
    "file_path": "uploads/user_123/quarterly_report.pdf",
    "file_size": 2048576,
    "file_type": "pdf",
    "upload_date": "2024-01-15T15:45:00Z",
    "is_processed": true,
    "processing_status": "completed",
    "chunks_count": 15,
    "insights": {
      "business_category": "financial",
      "sentiment_score": 0.75,
      "key_topics": ["revenue", "growth", "market analysis"],
      "summary": "Quarterly financial report showing 15% growth..."
    },
    "metadata": {
      "pages": 25,
      "word_count": 3500,
      "language": "en"
    }
  }
}
```

### Delete Document

```http
DELETE /documents/456
Authorization: Required
```

**Response:**
```json
{
  "success": true,
  "message": "Document deleted successfully"
}
```

## Analytics API

### Search Analytics

```http
GET /analytics/search?days=30&user_id=123
Authorization: Required (Admin)
```

**Response:**
```json
{
  "success": true,
  "analytics": {
    "period": "30 days",
    "total_searches": 1250,
    "unique_users": 45,
    "average_results_per_search": 12.5,
    "top_queries": [
      {"query": "financial analysis", "count": 156},
      {"query": "market research", "count": 142}
    ],
    "search_trends": [
      {"date": "2024-01-15", "searches": 42},
      {"date": "2024-01-16", "searches": 38}
    ],
    "performance_metrics": {
      "average_response_time_ms": 185,
      "cache_hit_rate": 68.5,
      "slow_queries_count": 12
    }
  }
}
```

### Document Analytics

```http
GET /analytics/documents?days=30
Authorization: Required (Admin)
```

**Response:**
```json
{
  "success": true,
  "analytics": {
    "period": "30 days",
    "total_documents": 245,
    "total_size_mb": 1250.5,
    "documents_by_type": {
      "pdf": 156,
      "docx": 78,
      "xlsx": 11
    },
    "processing_stats": {
      "processed": 240,
      "pending": 5,
      "failed": 0
    },
    "upload_trends": [
      {"date": "2024-01-15", "uploads": 8},
      {"date": "2024-01-16", "uploads": 12}
    ]
  }
}
```

## User Management API (Admin Only)

### List Users

```http
GET /admin/users?page=1&per_page=20&role=user
Authorization: Required (Admin)
```

**Response:**
```json
{
  "success": true,
  "users": [
    {
      "id": 123,
      "username": "john.doe@company.com",
      "email": "john.doe@company.com",
      "role": "user",
      "is_active": true,
      "created_at": "2024-01-10T09:00:00Z",
      "last_login": "2024-01-15T14:30:00Z",
      "document_count": 15,
      "search_count": 89
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 2,
    "total_items": 35
  }
}
```

### Create User

```http
POST /admin/users
Content-Type: application/json
Authorization: Required (Admin)

{
  "username": "jane.smith@company.com",
  "email": "jane.smith@company.com",
  "password": "secure_password_123",
  "role": "user"
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 124,
    "username": "jane.smith@company.com",
    "email": "jane.smith@company.com",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-15T16:00:00Z"
  },
  "message": "User created successfully"
}
```

### Update User

```http
PUT /admin/users/124
Content-Type: application/json
Authorization: Required (Admin)

{
  "role": "admin",
  "is_active": true
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 124,
    "username": "jane.smith@company.com",
    "role": "admin",
    "is_active": true,
    "updated_at": "2024-01-15T16:30:00Z"
  },
  "message": "User updated successfully"
}
```

## Security API (Admin Only)

### Security Dashboard

```http
GET /admin/security/dashboard?days=7
Authorization: Required (Admin)
```

**Response:**
```json
{
  "success": true,
  "security_summary": {
    "period": "7 days",
    "high_severity_events": [
      {
        "id": 789,
        "event_type": "multiple_failed_logins",
        "severity": "high",
        "ip_address": "192.168.1.100",
        "timestamp": "2024-01-15T12:00:00Z",
        "details": "5 failed login attempts in 2 minutes"
      }
    ],
    "medium_severity_events": [...],
    "low_severity_events": [...],
    "active_sessions": 25,
    "blocked_ips": ["192.168.1.100", "10.0.0.50"],
    "failed_login_attempts": 12,
    "rate_limit_violations": 3
  }
}
```

### Security Events

```http
GET /admin/security/events?page=1&severity=high&days=30
Authorization: Required (Admin)
```

**Response:**
```json
{
  "success": true,
  "events": [
    {
      "id": 789,
      "event_type": "sql_injection_attempt",
      "severity": "high",
      "ip_address": "192.168.1.100",
      "user_id": null,
      "user_agent": "Mozilla/5.0...",
      "timestamp": "2024-01-15T12:00:00Z",
      "details": "Blocked SQL injection in search query",
      "blocked": true
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_items": 45
  }
}
```

## Performance API (Admin Only)

### System Performance

```http
GET /admin/performance/system
Authorization: Required (Admin)
```

**Response:**
```json
{
  "success": true,
  "system_health": {
    "status": "healthy",
    "memory": {
      "process_memory_mb": 245.5,
      "system_memory_percent": 68.2,
      "peak_memory_mb": 289.1
    },
    "resources": {
      "cpu": {
        "usage_percent": 25.4,
        "core_count": 8
      },
      "disk": {
        "total_gb": 500.0,
        "used_gb": 125.5,
        "usage_percent": 25.1
      },
      "process": {
        "open_files": 45,
        "connections": 12,
        "threads": 8
      }
    },
    "warnings": []
  }
}
```

### Search Performance

```http
GET /admin/performance/search
Authorization: Required (Admin)
```

**Response:**
```json
{
  "success": true,
  "search_performance": {
    "faiss_optimizer": {
      "search_stats": {
        "total_searches": 1250,
        "avg_search_time": 0.185,
        "cache_hit_rate": 68.5
      },
      "cache_stats": {
        "cache_size": 890,
        "max_size": 1000,
        "hit_rate_percent": 68.5,
        "hits": 856,
        "misses": 394
      },
      "index_stats": {
        "total_vectors": 12500,
        "vector_dimension": 384,
        "is_trained": true
      }
    }
  }
}
```

### Database Performance

```http
GET /admin/performance/database
Authorization: Required (Admin)
```

**Response:**
```json
{
  "success": true,
  "database_performance": {
    "database_size_mb": 125.8,
    "cache_size_pages": 10000,
    "journal_mode": "WAL",
    "connection_pool_size": 8,
    "queries_executed": 15420,
    "avg_query_time_ms": 12.5,
    "slow_queries": 5,
    "slow_query_percentage": 0.32
  }
}
```

## Business Intelligence API

### KOBİ Dashboard

```http
GET /kobi/dashboard
Authorization: Required
```

**Response:**
```json
{
  "success": true,
  "dashboard_data": {
    "document_analytics": {
      "total_documents": 245,
      "processed_documents": 240,
      "pending_documents": 5,
      "avg_processing_time_minutes": 2.5
    },
    "search_analytics": {
      "total_searches": 1250,
      "avg_response_time_ms": 185,
      "popular_topics": ["financial", "marketing", "technical"]
    },
    "user_productivity": {
      "active_users": 45,
      "documents_per_user": 5.4,
      "searches_per_user": 27.8
    },
    "content_insights": {
      "content_categories": {
        "financial": 35,
        "marketing": 28,
        "technical": 22,
        "hr": 15
      },
      "sentiment_distribution": {
        "positive": 65,
        "neutral": 28,
        "negative": 7
      }
    }
  }
}
```

### Generate Report

```http
POST /kobi/generate_report
Content-Type: application/json
Authorization: Required

{
  "report_type": "executive",
  "format": "pdf",
  "date_range": {
    "from": "2024-01-01",
    "to": "2024-01-31"
  },
  "include_charts": true
}
```

**Response:**
```json
{
  "success": true,
  "report": {
    "id": "report_123",
    "download_url": "/kobi/download_report/executive_report_20240115.pdf",
    "filename": "executive_report_20240115.pdf",
    "generated_at": "2024-01-15T16:45:00Z",
    "expires_at": "2024-01-22T16:45:00Z"
  },
  "message": "Report generated successfully"
}
```

## Error Responses

All API endpoints return consistent error responses:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid query parameter",
    "details": {
      "field": "top_k",
      "reason": "Value must be between 1 and 100"
    }
  },
  "timestamp": "2024-01-15T16:00:00Z"
}
```

### Error Codes

- `AUTHENTICATION_REQUIRED`: User must be logged in
- `INSUFFICIENT_PERMISSIONS`: User doesn't have required permissions
- `VALIDATION_ERROR`: Invalid input parameters
- `NOT_FOUND`: Requested resource not found
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error
- `FILE_TOO_LARGE`: Uploaded file exceeds size limit
- `UNSUPPORTED_FILE_TYPE`: File type not supported

## Rate Limiting

API endpoints are rate limited:

- **Search**: 100 requests per minute
- **Upload**: 10 requests per minute
- **General**: 1000 requests per hour

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642259400
```

## Webhooks

Configure webhooks for real-time notifications:

### Document Processing Complete

```json
{
  "event": "document.processed",
  "timestamp": "2024-01-15T16:00:00Z",
  "data": {
    "document_id": 456,
    "filename": "quarterly_report.pdf",
    "processing_time_seconds": 45,
    "chunks_created": 15,
    "status": "completed"
  }
}
```

### Security Alert

```json
{
  "event": "security.alert",
  "timestamp": "2024-01-15T16:00:00Z",
  "data": {
    "event_type": "multiple_failed_logins",
    "severity": "high",
    "ip_address": "192.168.1.100",
    "details": "5 failed login attempts detected"
  }
}
```

## SDK Examples

### Python SDK

```python
import requests

class DeepSearchClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.session = requests.Session()
        self.login(username, password)
    
    def login(self, username, password):
        response = self.session.post(f"{self.base_url}/login", json={
            "username": username,
            "password": password
        })
        if response.status_code != 200:
            raise Exception("Login failed")
    
    def search(self, query, top_k=10, filters=None):
        response = self.session.post(f"{self.base_url}/search", json={
            "query": query,
            "top_k": top_k,
            "filters": filters or {}
        })
        return response.json()
    
    def upload_document(self, file_path, auto_index=True):
        with open(file_path, 'rb') as f:
            response = self.session.post(f"{self.base_url}/documents/upload", 
                files={'file': f},
                data={'auto_index': auto_index}
            )
        return response.json()

# Usage
client = DeepSearchClient("http://localhost:8080", "user@example.com", "password")
results = client.search("artificial intelligence")
print(results)
```

### JavaScript SDK

```javascript
class DeepSearchClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }
    
    async login(username, password) {
        const response = await fetch(`${this.baseUrl}/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password}),
            credentials: 'include'
        });
        return response.json();
    }
    
    async search(query, topK = 10, filters = {}) {
        const response = await fetch(`${this.baseUrl}/search`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({
                query,
                top_k: topK,
                filters
            })
        });
        return response.json();
    }
}

// Usage
const client = new DeepSearchClient('http://localhost:8080');
await client.login('user@example.com', 'password');
const results = await client.search('artificial intelligence');
console.log(results);
```

---

**API Version**: 1.0  
**Last Updated**: January 15, 2024  
**Contact**: api-support@deepsearch.com