import { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: 'admin' | 'manager' | 'user';
}

export default function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const { isAuthenticated, user, isLoading } = useAuth();
  const location = useLocation();

  // Show loading while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--primary-color)] mx-auto mb-4"></div>
          <p className="text-gray-600">Kimlik doğrulanıyor...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role permissions if required
  if (requiredRole && user) {
    const hasPermission = checkRolePermission(user.role, requiredRole);
    
    if (!hasPermission) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 18.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Erişim Reddedildi</h1>
            <p className="text-gray-600 mb-4">
              Bu sayfaya erişmek için {getRoleDisplayName(requiredRole)} yetkisine sahip olmanız gerekiyor.
            </p>
            <p className="text-sm text-gray-500">
              Mevcut rolünüz: {getRoleDisplayName(user.role)}
            </p>
          </div>
        </div>
      );
    }
  }

  return <>{children}</>;
}

// Role hierarchy: admin > manager > user
function checkRolePermission(userRole: string, requiredRole: string): boolean {
  const roleHierarchy = {
    admin: 3,
    manager: 2,
    user: 1
  };
  
  const userLevel = roleHierarchy[userRole as keyof typeof roleHierarchy] || 0;
  const requiredLevel = roleHierarchy[requiredRole as keyof typeof roleHierarchy] || 0;
  
  return userLevel >= requiredLevel;
}

function getRoleDisplayName(role: string): string {
  const roleNames = {
    admin: 'Admin',
    manager: 'Yönetici', 
    user: 'Kullanıcı'
  };
  
  return roleNames[role as keyof typeof roleNames] || role;
}