export interface User {
  id: number;
  username: string;
  email: string | null;
  full_name: string | null;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  last_login: string | null;
  avatar?: string | null;
}

export interface CreateUserRequest {
  username: string;
  password: string;
  email?: string;
  full_name?: string;
  is_admin: boolean;
}

export interface UpdateUserRequest {
  email?: string;
  full_name?: string;
  is_active?: boolean;
  is_admin?: boolean;
}

export interface UsersListResponse {
  total: number;
  users: User[];
}

