import { Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';

export interface UserSession {
  userId: string;
  displayName: string;
  department: 'HR' | 'Employee';
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly STORAGE_KEY = 'cko_user';

  private _user = signal<UserSession | null>(this.loadFromStorage());

  readonly user = this._user.asReadonly();

  constructor(private router: Router) {}

  get isHR(): boolean {
    return this._user()?.department === 'HR';
  }

  get userId(): string {
    return this._user()?.userId ?? '';
  }

  get headers(): Record<string, string> {
    return { 'X-User-ID': this.userId };
  }

  login(displayName: string, department: 'HR' | 'Employee'): void {
    const userId = displayName.trim().toLowerCase().replace(/\s+/g, '_');
    const session: UserSession = { userId, displayName: displayName.trim(), department };
    this._user.set(session);
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(session));
    this.router.navigate(['/chat']);
  }

  logout(): void {
    this._user.set(null);
    localStorage.removeItem(this.STORAGE_KEY);
    this.router.navigate(['/login']);
  }

  isLoggedIn(): boolean {
    return this._user() !== null;
  }

  private loadFromStorage(): UserSession | null {
    try {
      const raw = localStorage.getItem(this.STORAGE_KEY);
      return raw ? (JSON.parse(raw) as UserSession) : null;
    } catch {
      return null;
    }
  }
}
