export interface Task {
  id: number;
  user_id: number;
  status: "queued" | "processing" | "ready_for_review" | "completed" | "failed";
  video_path: string;
  output_path: string | null;
  subtitle_path: string | null;
  progress: number;
  stage: string | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface TaskCreate {
  video_path: string;
  asr_model?: string;
  config?: Record<string, unknown>;
}

export interface QueueStatus {
  queue_length: number;
  current_task: Task | null;
}

export interface SubtitleSegment {
  text: string;
  start_time: number;
  end_time: number;
  translated_text: string | null;
}
