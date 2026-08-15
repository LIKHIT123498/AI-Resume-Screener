export interface Candidate {
  id: number;
  job_id: number;
  name: string;
  email: string;
  phone: string;
  overall_fit_score: number;
  skills_score: number;
  seniority_score: number;
  domain_score: number;
  extracted_skills: string[];
  red_flags: string[];
  is_shortlisted: number;
  one_line_summary: string;
}

export interface Job {
  id: number;
  title: string;
  department?: string;
  description: string;
  requirements: string;
  created_at: string;
  candidates?: Candidate[];
}