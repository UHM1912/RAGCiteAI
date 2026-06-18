import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RagService, QueryResponse } from './services/rag.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent implements OnInit {
  title = 'RAGCite AI';
  query: string = '';
  loading: boolean = false;
  response: QueryResponse | null = null;
  error: string | null = null;
  isDarkMode: boolean = true;

  constructor(private ragService: RagService) {}

  ngOnInit(): void {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
      this.isDarkMode = false;
      document.body.classList.add('light-theme');
    }
  }

  toggleTheme(): void {
    this.isDarkMode = !this.isDarkMode;
    if (this.isDarkMode) {
      document.body.classList.remove('light-theme');
      localStorage.setItem('theme', 'dark');
    } else {
      document.body.classList.add('light-theme');
      localStorage.setItem('theme', 'light');
    }
  }

  onSearch(): void {
    if (!this.query.trim()) {
      return;
    }

    this.loading = true;
    this.error = null;
    this.response = null;

    this.ragService.search(this.query).subscribe({
      next: (res) => {
        this.response = res;
        this.loading = false;
      },
      error: (err) => {
        console.error(err);
        this.error = 'Unable to fetch response. Please verify the backend API is running.';
        this.loading = false;
      }
    });
  }

  clearSearch(): void {
    this.query = '';
    this.response = null;
    this.error = null;
  }
}

