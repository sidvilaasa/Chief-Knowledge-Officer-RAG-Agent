import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-typing-indicator',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bubble assistant">
      <div class="typing">
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
      </div>
    </div>
  `,
  styles: [`
    .bubble {
      max-width: 80%;
      padding: 16px;
      border-radius: 12px;
      font-size: 15px;
      line-height: 1.6;
      background-color: var(--assistant-bubble);
      color: var(--assistant-text);
      align-self: flex-start;
      margin-bottom: 24px;
      border-bottom-left-radius: 4px;
    }
    .typing {
      display: flex;
      gap: 4px;
      padding: 4px 8px;
    }
    .dot {
      width: 6px;
      height: 6px;
      background-color: var(--text-secondary);
      border-radius: 50%;
      animation: bounce 1.4s infinite ease-in-out both;
    }
    .dot:nth-child(1) { animation-delay: -0.32s; }
    .dot:nth-child(2) { animation-delay: -0.16s; }
    @keyframes bounce {
      0%, 80%, 100% { transform: scale(0); }
      40% { transform: scale(1); }
    }
  `]
})
export class TypingIndicatorComponent {}
