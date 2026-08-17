import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: 'login', loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent) },
  { path: 'chat', loadComponent: () => import('./pages/chat/chat.component').then(m => m.ChatComponent), canActivate: [authGuard] },
  { path: '', redirectTo: 'chat', pathMatch: 'full' },
  { path: '**', redirectTo: 'chat' }
];
