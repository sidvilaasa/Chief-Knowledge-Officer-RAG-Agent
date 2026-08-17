import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AuthService } from './auth.service';

export interface ChatMessage {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  created_at?: string;
}

export interface Session {
  id: string;
  user_id: string;
  title: string | null;
  created_at: string;
  last_used_at: string;
}

export interface QueryRequest {
  question: string;
  session_id?: string;
}

export interface QueryResponse {
  question: string;
  session_id: string;
  session_title: string | null;
  routing: string;
  internal?: { answer: string; citations: string[] } | null;
  web?: { answer: string; citations: string[] } | null;
  casual_answer?: string | null;
}

export interface UploadResponse {
  message: string;
  document_id: string;
  storage_path: string;
}

export interface AuthRequest {
  username: string;
  password: string;
  department?: 'HR' | 'Employee';
}

export interface AuthResponse {
  message: string;
  username: string;
  department: 'HR' | 'Employee';
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = environment.apiBase;

  constructor(private http: HttpClient, private auth: AuthService) {}

  private get headers(): HttpHeaders {
    return new HttpHeaders(this.auth.headers);
  }

  // ── Auth ──────────────────────────────────────────────────────────────────

  signup(req: AuthRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.base}/auth/signup`, req);
  }

  login(req: AuthRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.base}/auth/login`, req);
  }

  // ── Query ─────────────────────────────────────────────────────────────────

  sendQuery(req: QueryRequest): Observable<QueryResponse> {
    return this.http.post<QueryResponse>(`${this.base}/query`, req, {
      headers: this.headers,
    });
  }

  // ── Sessions ──────────────────────────────────────────────────────────────

  listSessions(): Observable<{ sessions: Session[]; total: number }> {
    return this.http.get<{ sessions: Session[]; total: number }>(
      `${this.base}/sessions`,
      { headers: this.headers }
    );
  }

  getSessionMessages(sessionId: string): Observable<{ session_id: string; messages: ChatMessage[]; total: number }> {
    return this.http.get<{ session_id: string; messages: ChatMessage[]; total: number }>(
      `${this.base}/sessions/${sessionId}/messages`,
      { headers: this.headers }
    );
  }

  deleteSession(sessionId: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/sessions/${sessionId}`, {
      headers: this.headers,
    });
  }

  // ── Documents ─────────────────────────────────────────────────────────────

  uploadUserDoc(file: File): Observable<UploadResponse> {
    const form = new FormData();
    form.append('file', file);
    return this.http.post<UploadResponse>(`${this.base}/documents/upload-user-doc`, form, {
      headers: this.headers,
    });
  }

  uploadGlobalDoc(file: File): Observable<UploadResponse> {
    const form = new FormData();
    form.append('file', file);
    return this.http.post<UploadResponse>(`${this.base}/documents/upload-global-doc`, form, {
      headers: this.headers,
    });
  }
}
