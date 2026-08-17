import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../core/services/auth.service';
import { ApiService, AuthRequest } from '../../core/services/api.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  isSignUp = signal(false);
  username = signal('');
  password = signal('');
  department = signal<'HR' | 'Employee'>('Employee');
  errorMsg = signal('');
  isLoading = signal(false);

  constructor(private auth: AuthService, private api: ApiService) {}

  setDepartment(dept: 'HR' | 'Employee') {
    this.department.set(dept);
  }
  
  toggleMode() {
    this.isSignUp.update(v => !v);
    this.errorMsg.set('');
  }

  submit() {
    if (!this.username().trim() || !this.password().trim()) {
      this.errorMsg.set('Username and password are required');
      return;
    }

    this.isLoading.set(true);
    this.errorMsg.set('');

    const req: AuthRequest = {
      username: this.username().trim(),
      password: this.password()
    };

    if (this.isSignUp()) {
      req.department = this.department();
      this.api.signup(req).subscribe({
        next: (res) => {
          this.auth.login(res.username, res.department);
          this.isLoading.set(false);
        },
        error: (err) => {
          this.errorMsg.set(err.error?.detail || 'Registration failed');
          this.isLoading.set(false);
        }
      });
    } else {
      this.api.login(req).subscribe({
        next: (res) => {
          this.auth.login(res.username, res.department);
          this.isLoading.set(false);
        },
        error: (err) => {
          this.errorMsg.set(err.error?.detail || 'Login failed');
          this.isLoading.set(false);
        }
      });
    }
  }
}
