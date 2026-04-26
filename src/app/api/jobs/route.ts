import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

// GET /api/jobs — public listing
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const search = searchParams.get('search')
  const category = searchParams.get('category')
  const work_mode = searchParams.get('work_mode')
  const job_type = searchParams.get('job_type')
  const limit = parseInt(searchParams.get('limit') || '20')
  const offset = parseInt(searchParams.get('offset') || '0')

  let query = supabase
    .from('jobs')
    .select('*', { count: 'exact' })
    .eq('is_active', true)
    .order('is_featured', { ascending: false })
    .order('posted_at', { ascending: false })
    .range(offset, offset + limit - 1)

  if (search) query = query.textSearch('fts', search, { type: 'websearch' })
  if (category && category !== 'All') query = query.eq('category', category)
  if (work_mode && work_mode !== 'All') query = query.eq('work_mode', work_mode)
  if (job_type && job_type !== 'All') query = query.eq('job_type', job_type)

  const { data, error, count } = await query

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  return NextResponse.json({ jobs: data, count, limit, offset })
}

// POST /api/jobs — admin create job
export async function POST(request: NextRequest) {
  // Verify admin secret
  const adminSecret = request.headers.get('x-admin-secret')
  if (adminSecret !== process.env.ADMIN_SECRET) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    const body = await request.json()

    // Validate required fields
    const required = ['title', 'company', 'location', 'work_mode', 'job_type', 'experience', 'description', 'apply_url', 'apply_source', 'category']
    const missing = required.filter(field => !body[field])
    if (missing.length > 0) {
      return NextResponse.json({ error: `Missing fields: ${missing.join(', ')}` }, { status: 400 })
    }

    const { data, error } = await supabase
      .from('jobs')
      .insert([{
        title: body.title,
        company: body.company,
        logo_url: body.logo_url || null,
        location: body.location,
        work_mode: body.work_mode,
        job_type: body.job_type,
        experience: body.experience,
        salary_min: body.salary_min || null,
        salary_max: body.salary_max || null,
        salary_text: body.salary_text || null,
        description: body.description,
        responsibilities: body.responsibilities || [],
        requirements: body.requirements || [],
        skills: body.skills || [],
        apply_url: body.apply_url,
        apply_source: body.apply_source,
        category: body.category,
        is_featured: body.is_featured || false,
        is_active: true,
      }])
      .select()
      .single()

    if (error) throw error

    return NextResponse.json({ success: true, job: data }, { status: 201 })
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
