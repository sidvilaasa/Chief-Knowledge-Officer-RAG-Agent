import { Component, ElementRef, OnInit, ViewChild, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService, ChatMessage } from '../../core/services/api.service';
import { SidebarComponent } from '../../components/sidebar/sidebar.component';
import { MessageBubbleComponent } from '../../components/message-bubble/message-bubble.component';
import { TypingIndicatorComponent } from '../../components/typing-indicator/typing-indicator.component';
import { UploadDialogComponent } from '../../components/upload-dialog/upload-dialog.component';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    SidebarComponent,
    MessageBubbleComponent,
    TypingIndicatorComponent,
    UploadDialogComponent
  ],
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent implements OnInit {
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef;
  @ViewChild(SidebarComponent) private sidebar!: SidebarComponent;

  messages = signal<ChatMessage[]>([]);
  inputMessage = '';
  isLoading = signal(false);
  currentSessionId = signal<string | null>(null);
  showUploadDialog = false;
  uploadScope: 'user' | 'global' = 'user';
  sidebarOpen = signal(false);

  toggleSidebar() {
    this.sidebarOpen.update(v => !v);
  }

  closeSidebar() {
    this.sidebarOpen.set(false);
  }

  constructor(private api: ApiService, public auth: AuthService) {}

  ngOnInit(): void {
    // Sidebar loads sessions via signals (zoneless CD).
  }

  startNewChat() {
    this.currentSessionId.set(null);
    this.messages.set([]);
    this.isLoading.set(false);
  }

  loadSession(sessionId: string) {
    this.currentSessionId.set(sessionId);
    this.isLoading.set(true);
    this.messages.set([]);

    this.api.getSessionMessages(sessionId).subscribe({
      next: (res) => {
        this.messages.set(res.messages ?? []);
        this.isLoading.set(false);
        this.scrollToBottom();
      },
      error: () => {
        this.isLoading.set(false);
      }
    });
  }

  sendMessage() {
    const text = this.inputMessage.trim();
    if (!text || this.isLoading()) return;

    this.messages.update(msgs => [...msgs, { role: 'user', content: text }]);
    this.inputMessage = '';
    this.isLoading.set(true);
    this.scrollToBottom();

    this.api.sendQuery({
      question: text,
      session_id: this.currentSessionId() || undefined
    }).subscribe({
      next: (res) => {
        this.isLoading.set(false);
        this.currentSessionId.set(res.session_id);

        const citations = [
          ...(res.internal?.citations ?? []),
          ...(res.web?.citations ?? [])
        ].filter((c, i, arr) => c && arr.indexOf(c) === i);

        let answerText = res.casual_answer || '';
        if (res.internal?.answer && res.web?.answer) {
          answerText = `${res.internal.answer}\n\n${res.web.answer}`;
        } else if (res.internal?.answer) {
          answerText = res.internal.answer;
        } else if (res.web?.answer) {
          answerText = res.web.answer;
        }

        this.messages.update(msgs => [...msgs, {
          role: 'assistant',
          content: answerText,
          citations,
          agent_name: res.agent_name || null
        }]);

        this.scrollToBottom();

        if (this.sidebar) {
          this.sidebar.loadSessions();
        }
      },
      error: () => {
        this.isLoading.set(false);
        this.messages.update(msgs => [...msgs, {
          role: 'assistant',
          content: 'Sorry, there was an error processing your request.'
        }]);
        this.scrollToBottom();
      }
    });
  }

  openUpload(scope: 'user' | 'global') {
    this.uploadScope = scope;
    this.showUploadDialog = true;
  }

  closeUpload() {
    this.showUploadDialog = false;
  }

  private scrollToBottom() {
    setTimeout(() => {
      try {
        if (this.messagesContainer) {
          this.messagesContainer.nativeElement.scrollTop = this.messagesContainer.nativeElement.scrollHeight;
        }
      } catch {
        // ignore
      }
    }, 100);
  }
}
