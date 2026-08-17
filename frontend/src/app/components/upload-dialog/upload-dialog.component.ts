import { Component, EventEmitter, Output, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-upload-dialog',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="modal-backdrop" (click)="close.emit()">
      <div class="modal-content" (click)="$event.stopPropagation()">
        
        <div class="modal-header">
          <h2>Upload Document</h2>
          <button class="icon-btn" (click)="close.emit()">
            <span class="material-icons">close</span>
          </button>
        </div>

        <div class="tabs" *ngIf="isHR">
          <button [class.active]="scope === 'user'" (click)="scope = 'user'">My Documents</button>
          <button [class.active]="scope === 'global'" (click)="scope = 'global'">Global Documents</button>
        </div>

        <div class="modal-body">
          <div 
            class="drop-zone" 
            [class.dragover]="isDragging"
            (dragover)="onDragOver($event)"
            (dragleave)="onDragLeave($event)"
            (drop)="onDrop($event)"
            (click)="fileInput.click()">
            
            <span class="material-icons upload-icon">cloud_upload</span>
            <p *ngIf="!selectedFile">Click or drag file here to upload</p>
            <p *ngIf="selectedFile" class="file-name">{{ selectedFile.name }}</p>
            <p class="help-text">Supports .pdf, .txt, .docx, .md</p>
            
            <input #fileInput type="file" hidden (change)="onFileSelected($event)" accept=".pdf,.txt,.docx,.doc,.md">
          </div>

          <div class="status-uploading" *ngIf="isUploading && !uploadSuccess">
            <span class="material-icons spin">sync</span>
            Uploading and processing...
          </div>

          <div class="status-success" *ngIf="uploadSuccess">
            <span class="material-icons">check_circle</span>
            <div>
              <div class="success-title">Document uploaded successfully!</div>
              <div class="success-file">{{ selectedFile?.name }}</div>
            </div>
          </div>

          <div class="status-error" *ngIf="errorMsg">
            <span class="material-icons">error_outline</span>
            {{ errorMsg }}
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-cancel" (click)="close.emit()">Cancel</button>
          <button class="btn-primary" [disabled]="!selectedFile || isUploading" (click)="upload()">
            {{ isUploading ? 'Uploading...' : 'Upload' }}
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .modal-backdrop {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    }
    .modal-content {
      background: var(--surface-color);
      border-radius: 12px;
      width: 100%;
      max-width: 500px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.2);
      border: 1px solid var(--border-color);
      overflow: hidden;
    }
    .modal-header {
      padding: 20px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border-color);
    }
    .modal-header h2 {
      font-size: 18px;
      font-weight: 600;
    }
    .icon-btn {
      color: var(--text-secondary);
      padding: 4px;
      border-radius: 4px;
    }
    .icon-btn:hover {
      background: var(--bg-color);
      color: var(--text-primary);
    }
    
    .tabs {
      display: flex;
      border-bottom: 1px solid var(--border-color);
      background: var(--bg-color);
    }
    .tabs button {
      flex: 1;
      padding: 12px;
      font-weight: 500;
      color: var(--text-secondary);
      border-bottom: 2px solid transparent;
    }
    .tabs button.active {
      color: var(--primary-color);
      border-bottom-color: var(--primary-color);
    }
    .tabs button:hover:not(.active) {
      background: var(--surface-color);
    }

    .modal-body {
      padding: 24px;
    }

    .drop-zone {
      border: 2px dashed var(--border-color);
      border-radius: 8px;
      padding: 40px 20px;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s;
      background: var(--bg-color);
    }
    .drop-zone:hover, .drop-zone.dragover {
      border-color: var(--primary-color);
      background: var(--sidebar-color);
    }
    
    .upload-icon {
      font-size: 48px;
      color: var(--text-secondary);
      margin-bottom: 16px;
    }
    .file-name {
      font-weight: 500;
      color: var(--primary-color);
      margin-bottom: 8px;
    }
    .help-text {
      font-size: 12px;
      color: var(--text-secondary);
      margin-top: 8px;
    }

    .status {
      margin-top: 16px;
      font-size: 14px;
      text-align: center;
      color: var(--text-secondary);
    }

    .status-uploading {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin-top: 16px;
      font-size: 14px;
      color: var(--text-secondary);
    }
    .spin {
      animation: spin 1s linear infinite;
      font-size: 18px;
    }
    @keyframes spin {
      from { transform: rotate(0deg); }
      to   { transform: rotate(360deg); }
    }

    .status-success {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-top: 16px;
      padding: 14px 16px;
      background: #f0fdf4;
      border: 1px solid #86efac;
      border-radius: 8px;
      color: #166534;
    }
    .status-success .material-icons {
      font-size: 28px;
      color: #22c55e;
      flex-shrink: 0;
    }
    .success-title {
      font-size: 14px;
      font-weight: 600;
    }
    .success-file {
      font-size: 12px;
      opacity: 0.8;
      margin-top: 2px;
    }

    .status-error {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 16px;
      padding: 12px 16px;
      background: #fef2f2;
      border: 1px solid #fca5a5;
      border-radius: 8px;
      font-size: 14px;
      color: #991b1b;
    }
    .status-error .material-icons {
      font-size: 18px;
      color: #ef4444;
      flex-shrink: 0;
    }

    .modal-footer {
      padding: 16px 24px;
      border-top: 1px solid var(--border-color);
      display: flex;
      justify-content: flex-end;
      gap: 12px;
      background: var(--bg-color);
    }

    .btn-cancel {
      padding: 8px 16px;
      border-radius: 6px;
      font-weight: 500;
      color: var(--text-primary);
    }
    .btn-cancel:hover {
      background: var(--surface-color);
    }

    .btn-primary {
      padding: 8px 16px;
      border-radius: 6px;
      font-weight: 500;
      background: var(--primary-color);
      color: white;
    }
    .btn-primary:hover:not([disabled]) {
      background: var(--primary-hover);
    }
    .btn-primary[disabled] {
      opacity: 0.5;
      cursor: not-allowed;
    }

    /* ── Mobile ──────────────────────────────────────────────── */
    @media (max-width: 600px) {
      .modal-content {
        max-width: 100%;
        width: 100%;
        margin: 0;
        border-radius: 16px 16px 0 0;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
      }

      .modal-backdrop {
        align-items: flex-end;
      }

      .modal-body {
        padding: 16px;
      }

      .drop-zone {
        padding: 28px 16px;
      }

      .modal-footer {
        padding: 12px 16px;
      }
    }
  `]
})
export class UploadDialogComponent implements OnInit {
  @Input() initialScope: 'user' | 'global' = 'user';
  @Output() close = new EventEmitter<void>();
  
  isHR = false;
  scope: 'user' | 'global' = 'user';
  
  isDragging = false;
  selectedFile: File | null = null;
  isUploading = false;
  uploadSuccess = false;
  errorMsg = '';

  constructor(private auth: AuthService, private api: ApiService) {
    this.isHR = this.auth.isHR;
  }

  ngOnInit() {
    this.scope = this.initialScope;
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    this.isDragging = false;
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    this.isDragging = false;
    if (event.dataTransfer?.files?.length) {
      this.selectedFile = event.dataTransfer.files[0];
      this.uploadSuccess = false;
      this.errorMsg = '';
    }
  }

  onFileSelected(event: any) {
    if (event.target.files?.length) {
      this.selectedFile = event.target.files[0];
      this.uploadSuccess = false;
      this.errorMsg = '';
    }
  }

  upload() {
    if (!this.selectedFile) return;
    
    this.isUploading = true;
    this.uploadSuccess = false;
    this.errorMsg = '';

    const req$ = this.scope === 'global' 
      ? this.api.uploadGlobalDoc(this.selectedFile)
      : this.api.uploadUserDoc(this.selectedFile);

    req$.subscribe({
      next: (res) => {
        this.isUploading = false;
        this.uploadSuccess = true;
        setTimeout(() => this.close.emit(), 2000);
      },
      error: (err) => {
        this.isUploading = false;
        this.errorMsg = 'Upload failed: ' + (err.error?.detail || err.message);
      }
    });
  }
}
