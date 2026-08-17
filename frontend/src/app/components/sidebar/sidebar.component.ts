import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService, Session } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { ThemeService } from '../../core/services/theme.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="sidebar">
      <!-- Header -->
      <div class="header">
        <button class="new-chat-btn" (click)="onNewChat()">
          <span class="material-icons">add</span>
          New Chat
        </button>
      </div>

      <!-- Session List -->
      <div class="session-list">
        <div class="section-title">Recent Chats</div>
        
        <div class="session-item" *ngFor="let s of sessions" 
             [class.active]="s.id === currentSessionId"
             (click)="onSelectSession(s.id)">
          <span class="material-icons session-icon">chat_bubble_outline</span>
          <span class="session-title">{{ s.title || 'New Conversation' }}</span>
          
          <button class="delete-btn" (click)="onDeleteSession(s.id, $event)" title="Delete Chat">
            <span class="material-icons">delete_outline</span>
          </button>
        </div>
        
        <div class="empty-state" *ngIf="sessions.length === 0">
          No recent chats
        </div>
      </div>

      <!-- Footer -->
      <div class="footer">
        <div class="user-info">
          <div class="avatar">{{ userInitials }}</div>
          <div class="details">
            <div class="name">{{ displayName }}</div>
            <div class="dept">{{ department }}</div>
          </div>
        </div>
        
        <div class="footer-actions">
          <button class="icon-btn" (click)="theme.toggle()" [title]="theme.isDark ? 'Light Mode' : 'Dark Mode'">
            <span class="material-icons">{{ theme.isDark ? 'light_mode' : 'dark_mode' }}</span>
          </button>
          <button class="icon-btn" (click)="auth.logout()" title="Logout">
            <span class="material-icons">logout</span>
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .sidebar {
      width: 260px;
      height: 100%;
      background-color: var(--sidebar-color);
      display: flex;
      flex-direction: column;
      border-right: 1px solid var(--border-color);
    }
    
    .header {
      padding: 16px;
      display: flex;
      gap: 8px;
    }
    
    .new-chat-btn {
      flex: 1;
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 16px;
      background-color: var(--primary-color);
      color: white;
      border-radius: 8px;
      font-weight: 500;
      font-size: 14px;
    }
    .new-chat-btn:hover {
      background-color: var(--primary-hover);
    }
    
    .icon-btn {
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
      color: var(--text-primary);
      background-color: var(--bg-color);
      border: 1px solid var(--border-color);
    }
    .icon-btn:hover {
      background-color: var(--surface-color);
    }
    
    .session-list {
      flex: 1;
      overflow-y: auto;
      padding: 0 12px;
    }
    
    .section-title {
      font-size: 12px;
      font-weight: 600;
      color: var(--text-secondary);
      padding: 12px;
      margin-top: 8px;
    }
    
    .session-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px;
      border-radius: 8px;
      cursor: pointer;
      color: var(--text-primary);
      margin-bottom: 4px;
      position: relative;
    }
    .session-item:hover {
      background-color: var(--bg-color);
    }
    .session-item.active {
      background-color: var(--surface-color);
      font-weight: 500;
    }
    
    .session-icon {
      font-size: 18px;
      color: var(--text-secondary);
    }
    
    .session-title {
      flex: 1;
      font-size: 14px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    
    .delete-btn {
      display: none;
      color: var(--text-secondary);
      padding: 4px;
      border-radius: 4px;
    }
    .session-item:hover .delete-btn {
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .delete-btn:hover {
      color: var(--danger-color);
      background-color: var(--bg-color);
    }
    .delete-btn .material-icons {
      font-size: 18px;
    }

    .empty-state {
      padding: 12px;
      font-size: 13px;
      color: var(--text-secondary);
      text-align: center;
    }
    
    .footer {
      padding: 16px;
      border-top: 1px solid var(--border-color);
    }
    
    .user-info {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
    }
    
    .avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background-color: var(--primary-color);
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 600;
      font-size: 14px;
    }
    
    .details {
      flex: 1;
      overflow: hidden;
    }
    .name {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-primary);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .dept {
      font-size: 12px;
      color: var(--text-secondary);
    }
    
    .footer-actions {
      display: flex;
      gap: 8px;
    }
    .footer-actions .icon-btn {
      flex: 1;
    }
  `]
})
export class SidebarComponent implements OnInit {
  @Input() currentSessionId: string | null = null;
  @Output() newChat = new EventEmitter<void>();
  @Output() selectSession = new EventEmitter<string>();
  
  sessions: Session[] = [];
  
  constructor(
    public auth: AuthService,
    public theme: ThemeService,
    private api: ApiService
  ) {}

  ngOnInit() {
    this.loadSessions();
  }

  get displayName() {
    return this.auth.user()?.displayName || 'User';
  }

  get userInitials() {
    const name = this.displayName;
    return name.substring(0, 2).toUpperCase();
  }

  get department() {
    return this.auth.isHR ? 'HR Department' : 'Employee';
  }

  loadSessions() {
    this.api.listSessions().subscribe({
      next: (res) => {
        this.sessions = res.sessions;
      }
    });
  }

  onNewChat() {
    this.newChat.emit();
  }

  onSelectSession(id: string) {
    this.selectSession.emit(id);
  }

  onDeleteSession(id: string, event: Event) {
    event.stopPropagation();
    if(confirm('Are you sure you want to delete this chat?')) {
      this.api.deleteSession(id).subscribe({
        next: () => {
          this.sessions = this.sessions.filter(s => s.id !== id);
          if (this.currentSessionId === id) {
            this.newChat.emit();
          }
        }
      });
    }
  }
}
