import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface SourceInfo {
  source: string;
  page: string;
  score: number;
  preview: string;
}

export interface QueryResponse {
  answer: string;
  confidence: number;
  sources: SourceInfo[];
  context?: string;
}

@Injectable({
  providedIn: 'root'
})
export class RagService {
  private apiUrl = 'http://localhost:8000/api/query';

  constructor(private http: HttpClient) {}

  search(query: string): Observable<QueryResponse> {
    return this.http.post<QueryResponse>(this.apiUrl, { query });
  }
}
