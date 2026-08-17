import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
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

  messages: ChatMessage[] = [];
  inputMessage = '';
  isLoading = false;
  currentSessionId: string | null = null;
  showUploadDialog = false;
  uploadScope: 'user' | 'global' = 'user';

  constructor(private api: ApiService, public auth: AuthService) {}

  ngOnInit(): void {
    // Start with empty state, let user start a new chat or pick one from sidebar
  }

  startNewChat() {
    this.currentSessionId = null;
    this.messages = [];
  }

  loadSession(sessionId: string) {
    this.currentSessionId = sessionId;
    this.isLoading = true;
    this.messages = [];
    
    this.api.getSessionMessages(sessionId).subscribe({
      next: (res) => {
        this.messages = res.messages;
        this.isLoading = false;
        this.scrollToBottom();
      },
      error: () => {
        this.isLoading = false;
      }
    });
  }

  sendMessage() {
    const text = this.inputMessage.trim();
    if (!text || this.isLoading) return;

    // Add user message to UI immediately
    this.messages.push({ role: 'user', content: text });
    this.inputMessage = '';
    this.isLoading = true;
    this.scrollToBottom();

    // Call API
    this.api.sendQuery({ question: text, session_id: this.currentSessionId || undefined }).subscribe({
      next: (res) => {
        this.isLoading = false;
        this.currentSessionId = res.session_id; // Set if it was a new session
        
        let answerText = res.casual_answer || '';
        let citations: string[] = [];
        
        if (res.internal) {
          answerText = res.internal.answer;
          citations = res.internal.citations;
        } else if (res.web) {
          answerText = res.web.answer;
          citations = res.web.citations;
        }

        this.messages.push({ 
          role: 'assistant', 
          content: answerText, 
          ...((citations && citations.length > 0) ? { citations } : {}) 
        } as any); // Type cast due to extra citations property not strictly in ChatMessage
        
        this.scrollToBottom();
        
        // Refresh sidebar to update title/new session
        if (this.sidebar) {
          this.sidebar.loadSessions();
        }
      },
      error: (err) => {
        this.isLoading = false;
        this.messages.push({ role: 'assistant', content: 'Sorry, there was an error processing your request.' });
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
      } catch(err) {}
    }, 100);
  }
}
