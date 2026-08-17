import { Component, Input, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-message-bubble',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="message-row" [class.user]="role === 'user'">
      <!-- Avatar -->
      <div class="avatar" *ngIf="role === 'assistant'">
        <span class="material-icons">smart_toy</span>
      </div>

      <div class="bubble" [class.user-bubble]="role === 'user'" [class.assistant-bubble]="role === 'assistant'">
        <!-- Parse content. In a real app we'd use marked.js for markdown, here we use simple line breaks -->
        <div class="content" [innerHTML]="formatContent(content)"></div>
        
        <div class="citations" *ngIf="citations && citations.length > 0">
          <div class="citation-title">Sources:</div>
          <div class="citation-chip" *ngFor="let cit of citations">
            <span class="material-icons cit-icon">description</span>
            {{ cit }}
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .message-row {
      display: flex;
      gap: 16px;
      margin-bottom: 24px;
      width: 100%;
    }
    .message-row.user {
      flex-direction: row-reverse;
    }
    
    .avatar {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background-color: var(--primary-color);
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .avatar .material-icons {
      font-size: 20px;
    }

    .bubble {
      max-width: 80%;
      padding: 16px;
      border-radius: 12px;
      font-size: 15px;
      line-height: 1.6;
    }

    .user-bubble {
      background-color: var(--user-bubble);
      color: var(--user-text);
      border-bottom-right-radius: 4px;
    }

    .assistant-bubble {
      background-color: var(--assistant-bubble);
      color: var(--assistant-text);
      border-bottom-left-radius: 4px;
    }

    .content {
      white-space: pre-wrap;
    }

    .citations {
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid rgba(128, 128, 128, 0.2);
    }
    
    .citation-title {
      font-size: 12px;
      font-weight: 600;
      color: var(--text-secondary);
      margin-bottom: 8px;
    }

    .citation-chip {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background-color: var(--bg-color);
      border: 1px solid var(--border-color);
      padding: 4px 8px;
      border-radius: 16px;
      font-size: 12px;
      color: var(--text-primary);
      margin-right: 8px;
      margin-bottom: 8px;
    }
    .cit-icon {
      font-size: 14px;
      color: var(--text-secondary);
    }
  `],
  encapsulation: ViewEncapsulation.None
})
export class MessageBubbleComponent {
  @Input({ required: true }) role!: 'user' | 'assistant';
  @Input({ required: true }) content!: string;
  @Input() citations?: string[] = [];

  formatContent(text: string): string {
    if (!text) return '';
    // Simple basic formatting: bolding (**text**)
    let html = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    return html;
  }
}
