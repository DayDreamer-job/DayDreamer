<?php
/**
 * Plugin Name: DayDreamer Poster
 * Plugin URI:  https://jobs.yourdomain.com
 * Description: Post new jobs directly to your DayDreamer Next.js site via Supabase. Fill the form → job appears instantly on your website.
 * Version:     1.0.0
 * Author:      DayDreamer
 */

if (!defined('ABSPATH')) exit;

// ── Register menu ─────────────────────────────────────────────
add_action('admin_menu', function () {
    add_menu_page(
        'DayDreamer',
        'DayDreamer',
        'manage_options',
        'DayDreamer',
        'DayDreamer_add_job_page',
        'dashicons-businessman',
        30
    );
    add_submenu_page('DayDreamer', 'Add New Job', 'Add New Job', 'manage_options', 'DayDreamer', 'DayDreamer_add_job_page');
    add_submenu_page('DayDreamer', 'Settings', 'Settings', 'manage_options', 'DayDreamer-settings', 'DayDreamer_settings_page');
    add_submenu_page('DayDreamer', 'Recent Jobs', 'Recent Jobs', 'manage_options', 'DayDreamer-recent', 'DayDreamer_recent_page');
});

// ── Settings page ─────────────────────────────────────────────
function DayDreamer_settings_page() {
    if (isset($_POST['DayDreamer_save_settings'])) {
        update_option('DayDreamer_supabase_url',      sanitize_text_field($_POST['supabase_url']));
        update_option('DayDreamer_supabase_anon_key', sanitize_text_field($_POST['supabase_anon_key']));
        update_option('DayDreamer_admin_secret',      sanitize_text_field($_POST['admin_secret']));
        echo '<div class="notice notice-success"><p>✅ Settings saved!</p></div>';
    }
    $url  = get_option('DayDreamer_supabase_url', '');
    $key  = get_option('DayDreamer_supabase_anon_key', '');
    $sec  = get_option('DayDreamer_admin_secret', '');
    ?>
    <div class="wrap">
        <h1>⚙️ DayDreamer Settings</h1>
        <form method="post">
            <table class="form-table">
                <tr>
                    <th><label for="supabase_url">Supabase URL</label></th>
                    <td>
                        <input type="text" id="supabase_url" name="supabase_url" value="<?php echo esc_attr($url); ?>" class="regular-text" placeholder="https://xxxx.supabase.co" />
                        <p class="description">Found in Supabase Dashboard → Settings → API</p>
                    </td>
                </tr>
                <tr>
                    <th><label for="supabase_anon_key">Supabase Anon Key</label></th>
                    <td>
                        <input type="text" id="supabase_anon_key" name="supabase_anon_key" value="<?php echo esc_attr($key); ?>" class="large-text" />
                        <p class="description">The public anon key — safe to use here</p>
                    </td>
                </tr>
                <tr>
                    <th><label for="admin_secret">Admin Secret</label></th>
                    <td>
                        <input type="password" id="admin_secret" name="admin_secret" value="<?php echo esc_attr($sec); ?>" class="regular-text" />
                        <p class="description">Your ADMIN_SECRET from .env.local</p>
                    </td>
                </tr>
            </table>
            <input type="hidden" name="DayDreamer_save_settings" value="1" />
            <?php submit_button('Save Settings'); ?>
        </form>
    </div>
    <?php
}

// ── Add Job page ──────────────────────────────────────────────
function DayDreamer_add_job_page() {
    $message = '';
    $message_type = 'success';

    if (isset($_POST['DayDreamer_submit'])) {
        $result = DayDreamer_post_job($_POST);
        if ($result['success']) {
            $message = '✅ Job posted successfully! It\'s now live on your website.';
        } else {
            $message_type = 'error';
            $message = '❌ Error: ' . esc_html($result['error']);
        }
    }

    $categories  = ['Technology','Design','Marketing','Finance','Sales','HR & Talent','Data & AI','Product'];
    $work_modes  = ['Remote','Hybrid','On-site'];
    $job_types   = ['Full-time','Part-time','Contract','Internship'];
    $sources     = ['Company','LinkedIn','Naukri','Indeed','JobFoundIt'];
    ?>
    <div class="wrap">
        <h1>➕ Add New Job to DayDreamer</h1>
        <?php if ($message): ?>
            <div class="notice notice-<?php echo $message_type; ?> is-dismissible"><p><?php echo $message; ?></p></div>
        <?php endif; ?>

        <style>
            .DayDreamer-form { max-width: 900px; margin-top: 20px; }
            .DayDreamer-form .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
            .DayDreamer-form .form-row.full { grid-template-columns: 1fr; }
            .DayDreamer-form label { display: block; font-weight: 600; margin-bottom: 4px; color: #1d2327; }
            .DayDreamer-form input, .DayDreamer-form select, .DayDreamer-form textarea {
                width: 100%; padding: 8px 12px; border: 1px solid #8c8f94; border-radius: 4px; font-size: 14px;
            }
            .DayDreamer-form textarea { min-height: 120px; resize: vertical; }
            .DayDreamer-form .section-title {
                font-size: 16px; font-weight: 700; color: #1d2327; border-bottom: 2px solid #f97316;
                padding-bottom: 6px; margin: 24px 0 16px; display: flex; align-items: center; gap: 8px;
            }
            .DayDreamer-submit { background: #f97316 !important; border-color: #ea580c !important; font-size: 16px !important; padding: 10px 30px !important; height: auto !important; }
            .DayDreamer-submit:hover { background: #ea580c !important; }
            .hint { color: #646970; font-size: 12px; margin-top: 3px; }
            .checkbox-row { display: flex; align-items: center; gap: 8px; }
            .checkbox-row input { width: auto; }
        </style>

        <form method="post" class="DayDreamer-form">

            <div class="section-title">📋 Basic Information</div>
            <div class="form-row">
                <div>
                    <label for="title">Job Title *</label>
                    <input type="text" id="title" name="title" required placeholder="e.g. Python Backend Developer" />
                </div>
                <div>
                    <label for="company">Company Name *</label>
                    <input type="text" id="company" name="company" required placeholder="e.g. Zomato" />
                </div>
            </div>
            <div class="form-row">
                <div>
                    <label for="location">Location *</label>
                    <input type="text" id="location" name="location" required placeholder="e.g. Bangalore, Karnataka" />
                </div>
                <div>
                    <label for="category">Category *</label>
                    <select id="category" name="category" required>
                        <?php foreach ($categories as $cat): ?>
                            <option value="<?php echo $cat; ?>"><?php echo $cat; ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
            </div>
            <div class="form-row">
                <div>
                    <label for="work_mode">Work Mode *</label>
                    <select id="work_mode" name="work_mode" required>
                        <?php foreach ($work_modes as $m): ?>
                            <option value="<?php echo $m; ?>"><?php echo $m; ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div>
                    <label for="job_type">Job Type *</label>
                    <select id="job_type" name="job_type" required>
                        <?php foreach ($job_types as $t): ?>
                            <option value="<?php echo $t; ?>"><?php echo $t; ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
            </div>
            <div class="form-row">
                <div>
                    <label for="experience">Experience Required *</label>
                    <input type="text" id="experience" name="experience" required placeholder="e.g. Fresher, 0-2 years, 3-5 years" />
                </div>
                <div>
                    <label for="salary_text">Salary (text)</label>
                    <input type="text" id="salary_text" name="salary_text" placeholder="e.g. 8-12 LPA or Not Disclosed" />
                </div>
            </div>

            <div class="section-title">🔗 Apply Link</div>
            <div class="form-row">
                <div>
                    <label for="apply_url">Apply URL *</label>
                    <input type="url" id="apply_url" name="apply_url" required placeholder="https://company.com/careers/job-123" />
                    <p class="hint">Full URL where candidates will be redirected to apply</p>
                </div>
                <div>
                    <label for="apply_source">Apply Source *</label>
                    <select id="apply_source" name="apply_source" required>
                        <?php foreach ($sources as $s): ?>
                            <option value="<?php echo $s; ?>"><?php echo $s; ?></option>
                        <?php endforeach; ?>
                    </select>
                    <p class="hint">Where the apply link goes to</p>
                </div>
            </div>

            <div class="section-title">📝 Job Details</div>
            <div class="form-row full">
                <div>
                    <label for="description">Job Description *</label>
                    <textarea id="description" name="description" required placeholder="Describe the role, team, what the candidate will do..."></textarea>
                </div>
            </div>
            <div class="form-row full">
                <div>
                    <label for="responsibilities">Key Responsibilities (one per line)</label>
                    <textarea id="responsibilities" name="responsibilities" placeholder="Design and implement REST APIs&#10;Write clean, testable code&#10;Collaborate with frontend team"></textarea>
                    <p class="hint">Each line becomes a separate responsibility point</p>
                </div>
            </div>
            <div class="form-row full">
                <div>
                    <label for="requirements">Requirements (one per line)</label>
                    <textarea id="requirements" name="requirements" placeholder="2+ years of Python experience&#10;Familiarity with REST APIs&#10;Strong problem-solving skills"></textarea>
                </div>
            </div>
            <div class="form-row full">
                <div>
                    <label for="skills">Skills (comma separated)</label>
                    <input type="text" id="skills" name="skills" placeholder="Python, FastAPI, PostgreSQL, Docker, Git" />
                    <p class="hint">Separate skills with commas</p>
                </div>
            </div>

            <div class="section-title">⚙️ Options</div>
            <div class="form-row">
                <div>
                    <label for="logo_url">Company Logo URL (optional)</label>
                    <input type="url" id="logo_url" name="logo_url" placeholder="https://company.com/logo.png" />
                    <p class="hint">Direct URL to company logo image</p>
                </div>
                <div style="padding-top: 28px;">
                    <div class="checkbox-row">
                        <input type="checkbox" id="is_featured" name="is_featured" value="1" />
                        <label for="is_featured" style="margin: 0;">⭐ Mark as Featured Job</label>
                    </div>
                    <p class="hint">Featured jobs appear at the top of listings and on the homepage</p>
                </div>
            </div>

            <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #ddd;">
                <input type="hidden" name="DayDreamer_submit" value="1" />
                <?php wp_nonce_field('DayDreamer_post_job'); ?>
                <button type="submit" class="button button-primary DayDreamer-submit">
                    🚀 Post Job to DayDreamer
                </button>
                <p class="hint" style="margin-top: 8px;">The job will appear on your website within seconds.</p>
            </div>
        </form>
    </div>
    <?php
}

// ── Recent Jobs page ──────────────────────────────────────────
function DayDreamer_recent_page() {
    $url = get_option('DayDreamer_supabase_url', '');
    $key = get_option('DayDreamer_supabase_anon_key', '');

    if (!$url || !$key) {
        echo '<div class="wrap"><h1>Recent Jobs</h1><div class="notice notice-warning"><p>Please configure Supabase settings first.</p></div></div>';
        return;
    }

    $response = wp_remote_get(
        $url . '/rest/v1/jobs?select=id,title,company,location,posted_at,is_active,is_featured&order=posted_at.desc&limit=20',
        ['headers' => ['apikey' => $key, 'Authorization' => 'Bearer ' . $key]]
    );

    $jobs = [];
    if (!is_wp_error($response)) {
        $jobs = json_decode(wp_remote_retrieve_body($response), true) ?: [];
    }
    ?>
    <div class="wrap">
        <h1>📋 Recent Jobs on DayDreamer</h1>
        <p>Showing last 20 jobs. <a href="<?php echo esc_url($url); ?>/project/default/editor" target="_blank">Open Supabase dashboard →</a></p>
        <table class="wp-list-table widefat fixed striped">
            <thead>
                <tr>
                    <th>Title</th>
                    <th>Company</th>
                    <th>Location</th>
                    <th>Posted</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <?php if (empty($jobs)): ?>
                    <tr><td colspan="5">No jobs found. <a href="<?php echo admin_url('admin.php?page=DayDreamer'); ?>">Add your first job →</a></td></tr>
                <?php else: foreach ($jobs as $job): ?>
                    <tr>
                        <td><strong><?php echo esc_html($job['title']); ?></strong>
                            <?php if ($job['is_featured']): ?> <span style="color:#f97316">⭐</span><?php endif; ?></td>
                        <td><?php echo esc_html($job['company']); ?></td>
                        <td><?php echo esc_html($job['location']); ?></td>
                        <td><?php echo esc_html(substr($job['posted_at'], 0, 10)); ?></td>
                        <td><?php echo $job['is_active'] ? '<span style="color:green">✅ Active</span>' : '<span style="color:red">❌ Inactive</span>'; ?></td>
                    </tr>
                <?php endforeach; endif; ?>
            </tbody>
        </table>
    </div>
    <?php
}

// ── Core: Post job to Supabase ────────────────────────────────
function DayDreamer_post_job($data) {
    if (!wp_verify_nonce($data['_wpnonce'] ?? '', 'DayDreamer_post_job')) {
        return ['success' => false, 'error' => 'Security check failed.'];
    }

    $url    = get_option('DayDreamer_supabase_url', '');
    $key    = get_option('DayDreamer_supabase_anon_key', '');

    if (!$url || !$key) {
        return ['success' => false, 'error' => 'Supabase not configured. Go to DayDreamer → Settings.'];
    }

    // Validate required
    $required = ['title','company','location','work_mode','job_type','experience','description','apply_url','apply_source','category'];
    foreach ($required as $field) {
        if (empty($data[$field])) {
            return ['success' => false, 'error' => "Field '$field' is required."];
        }
    }

    // Parse array fields
    $responsibilities = array_filter(array_map('trim', explode("\n", $data['responsibilities'] ?? '')));
    $requirements     = array_filter(array_map('trim', explode("\n", $data['requirements'] ?? '')));
    $skills_raw       = $data['skills'] ?? '';
    $skills           = $skills_raw ? array_filter(array_map('trim', explode(',', $skills_raw))) : [];

    $body = [
        'title'            => sanitize_text_field($data['title']),
        'company'          => sanitize_text_field($data['company']),
        'logo_url'         => !empty($data['logo_url']) ? esc_url_raw($data['logo_url']) : null,
        'location'         => sanitize_text_field($data['location']),
        'work_mode'        => sanitize_text_field($data['work_mode']),
        'job_type'         => sanitize_text_field($data['job_type']),
        'experience'       => sanitize_text_field($data['experience']),
        'salary_text'      => sanitize_text_field($data['salary_text'] ?? ''),
        'description'      => sanitize_textarea_field($data['description']),
        'responsibilities' => array_values($responsibilities),
        'requirements'     => array_values($requirements),
        'skills'           => array_values($skills),
        'apply_url'        => esc_url_raw($data['apply_url']),
        'apply_source'     => sanitize_text_field($data['apply_source']),
        'category'         => sanitize_text_field($data['category']),
        'is_featured'      => !empty($data['is_featured']),
        'is_active'        => true,
        'posted_at'        => date('c'),  // current timestamp
    ];

    $response = wp_remote_post(
        $url . '/rest/v1/jobs',
        [
            'headers' => [
                'Content-Type'  => 'application/json',
                'apikey'        => $key,
                'Authorization' => 'Bearer ' . $key,
                'Prefer'        => 'return=minimal',
            ],
            'body'    => json_encode($body),
            'timeout' => 15,
        ]
    );

    if (is_wp_error($response)) {
        return ['success' => false, 'error' => $response->get_error_message()];
    }

    $status_code = wp_remote_retrieve_response_code($response);
    if ($status_code === 201) {
        // Log it
        $log = get_option('DayDreamer_post_log', []);
        array_unshift($log, ['title' => $body['title'], 'company' => $body['company'], 'time' => date('Y-m-d H:i:s')]);
        update_option('DayDreamer_post_log', array_slice($log, 0, 50));
        return ['success' => true];
    }

    $body_response = wp_remote_retrieve_body($response);
    return ['success' => false, 'error' => "HTTP $status_code — $body_response"];
}

// ── Admin dashboard widget ────────────────────────────────────
add_action('wp_dashboard_setup', function () {
    wp_add_dashboard_widget('DayDreamer_widget', '🚀 DayDreamer — Quick Post', function () {
        $log = get_option('DayDreamer_post_log', []);
        echo '<p><a href="' . admin_url('admin.php?page=DayDreamer') . '" class="button button-primary">➕ Add New Job</a>';
        echo ' <a href="' . admin_url('admin.php?page=DayDreamer-recent') . '" class="button">📋 View Recent Jobs</a></p>';
        if (!empty($log)) {
            echo '<p><strong>Recently Posted:</strong></p><ul>';
            foreach (array_slice($log, 0, 5) as $entry) {
                echo '<li>' . esc_html($entry['title']) . ' @ ' . esc_html($entry['company']) . ' <small>(' . esc_html($entry['time']) . ')</small></li>';
            }
            echo '</ul>';
        }
    });
});
