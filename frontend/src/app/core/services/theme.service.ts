import { Injectable, signal } from '@angular/core';

export type Theme = 'light' | 'dark';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly STORAGE_KEY = 'cko_theme';
  private _theme = signal<Theme>(this.loadTheme());
  readonly theme = this._theme.asReadonly();

  get isDark(): boolean {
    return this._theme() === 'dark';
  }

  toggle(): void {
    const next: Theme = this._theme() === 'dark' ? 'light' : 'dark';
    this.applyTheme(next);
  }

  private applyTheme(t: Theme): void {
    this._theme.set(t);
    localStorage.setItem(this.STORAGE_KEY, t);
    document.documentElement.setAttribute('data-theme', t);
  }

  private loadTheme(): Theme {
    const saved = localStorage.getItem(this.STORAGE_KEY) as Theme | null;
    const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    const theme = saved ?? preferred;
    document.documentElement.setAttribute('data-theme', theme);
    return theme;
  }
}
