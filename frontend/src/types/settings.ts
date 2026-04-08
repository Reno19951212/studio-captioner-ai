export interface Settings {
  storage_base_path: string;
  default_asr_model: string;
  default_whisper_model: string;
  llm_api_base: string;
  llm_model: string;
}

export interface AvailableModels {
  asr_models: string[];
  whisper_sizes: string[];
}
