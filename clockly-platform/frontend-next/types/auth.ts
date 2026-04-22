export interface AuthUser {
  id: string;
  company_id: string;
  email: string;
  full_name: string;
  role: "owner" | "admin" | "manager" | "employee";
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface CompanyContext {
  id: string;
  name: string;
  slug: string;
  timezone: string;
}

export interface AuthPayload {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
  user: AuthUser;
  company: CompanyContext;
  permissions: string[];
}

export interface MePayload {
  user: AuthUser;
  company: CompanyContext;
  permissions: string[];
}

export interface LoginRequest {
  identifier: string;
  password: string;
}
