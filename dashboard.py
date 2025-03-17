import os
import json
import flask
from flask import Flask, render_template, jsonify, request
from datetime import datetime
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from analytics import Analytics
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - dashboard - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('dashboard')

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Create templates directory if it doesn't exist
if not os.path.exists('templates'):
    os.makedirs('templates')

# Create a base HTML template
with open('templates/layout.html', 'w') as f:
    f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lead Gen Bot Dashboard</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
    <style>
        body {
            padding-top: 2rem;
            background-color: #f8f9fa;
        }
        .card {
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .card-header {
            background-color: #343a40;
            color: white;
            font-weight: bold;
        }
        .stats-card {
            text-align: center;
            font-size: 1.5rem;
        }
        .stats-card .card-body {
            padding: 2rem;
        }
        .stats-number {
            font-size: 2.5rem;
            font-weight: bold;
            color: #007bff;
        }
        .stats-label {
            color: #6c757d;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center mb-4">Lead Gen Bot Dashboard</h1>
        
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        Bot Status
                    </div>
                    <div class="card-body">
                        <div id="bot-status">
                            <!-- Bot status will be loaded here -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <script>
        // Fetch bot status every 60 seconds
        function updateBotStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    const statusDiv = document.getElementById('bot-status');
                    let statusHtml = `
                        <div class="row">
                            <div class="col-md-3">
                                <div class="alert ${data.running ? 'alert-success' : 'alert-danger'}">
                                    <strong>Status:</strong> ${data.running ? 'Running' : 'Stopped'}
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="alert alert-info">
                                    <strong>Last Run:</strong> ${data.last_run}
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="alert alert-info">
                                    <strong>Next Action:</strong> ${data.next_action}
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="alert ${data.errors > 0 ? 'alert-warning' : 'alert-info'}">
                                    <strong>Errors:</strong> ${data.errors}
                                </div>
                            </div>
                        </div>
                    `;
                    statusDiv.innerHTML = statusHtml;
                });
        }
        
        // Initial update and set interval
        updateBotStatus();
        setInterval(updateBotStatus, 60000);
    </script>
    
    {% block scripts %}{% endblock %}
</body>
</html>''')

# Create an index template
with open('templates/index.html', 'w') as f:
    f.write('''{% extends "layout.html" %}

{% block content %}
<div class="row mb-4">
    <div class="col-md-3">
        <div class="card stats-card">
            <div class="card-body">
                <div class="stats-number">{{ stats.messages_sent }}</div>
                <div class="stats-label">Messages Sent</div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card stats-card">
            <div class="card-body">
                <div class="stats-number">{{ stats.responses }}</div>
                <div class="stats-label">Responses</div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card stats-card">
            <div class="card-body">
                <div class="stats-number">{{ stats.warm_leads }}</div>
                <div class="stats-label">Warm Leads</div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card stats-card">
            <div class="card-body">
                <div class="stats-number">{{ stats.response_rate }}%</div>
                <div class="stats-label">Response Rate</div>
            </div>
        </div>
    </div>
</div>

<div class="row mb-4">
    <div class="col-md-12">
        <div class="card">
            <div class="card-header">
                Daily Activity
            </div>
            <div class="card-body">
                <img src="data:image/png;base64,{{ charts.daily_activity }}" class="img-fluid" alt="Daily Activity Chart">
            </div>
        </div>
    </div>
</div>

<div class="row mb-4">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                Template Performance
            </div>
            <div class="card-body">
                <h5>Initial Templates</h5>
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>Template</th>
                            <th>Sent</th>
                            <th>Response Rate</th>
                            <th>Conversion Rate</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for template in templates.initial %}
                        <tr>
                            <td>{{ template.template_id }}</td>
                            <td>{{ template.sent_count }}</td>
                            <td>{{ "%.1f"|format(template.response_rate * 100) }}%</td>
                            <td>{{ "%.1f"|format(template.conversion_rate * 100) }}%</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                
                <h5 class="mt-4">Follow-up Templates</h5>
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>Template</th>
                            <th>Sent</th>
                            <th>Response Rate</th>
                            <th>Conversion Rate</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for template in templates.follow_up %}
                        <tr>
                            <td>{{ template.template_id }}</td>
                            <td>{{ template.sent_count }}</td>
                            <td>{{ "%.1f"|format(template.response_rate * 100) }}%</td>
                            <td>{{ "%.1f"|format(template.conversion_rate * 100) }}%</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                Optimization Recommendations
            </div>
            <div class="card-body">
                {% for category, recs in recommendations.items() %}
                <h5>{{ category.replace('_', ' ').title() }}</h5>
                <ul class="list-group mb-3">
                    {% for item, details in recs.items() %}
                    <li class="list-group-item">
                        <strong>{{ item }}:</strong> {{ details.recommendation }}
                    </li>
                    {% endfor %}
                </ul>
                {% endfor %}
            </div>
        </div>
    </div>
</div>

<div class="row mb-4">
    <div class="col-md-12">
        <div class="card">
            <div class="card-header">
                Platform Restrictions
            </div>
            <div class="card-body">
                <div class="row">
                    {% for restriction, count in restrictions.items() %}
                    <div class="col-md-3">
                        <div class="card mb-3 {% if count > 5 %}bg-warning{% else %}bg-light{% endif %}">
                            <div class="card-body text-center">
                                <h5 class="card-title">{{ restriction.replace('_', ' ').title() }}</h5>
                                <h2>{{ count }}</h2>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    // Refresh page every 5 minutes
    setTimeout(function() {
        location.reload();
    }, 300000);
</script>
{% endblock %}''')

# Generate a simple status data for the bot
def get_bot_status():
    try:
        # Check if the bot is running
        # This is a simple check, you might want to implement a more sophisticated method
        # For example, checking a PID file or a status file
        is_running = False
        last_run = "Unknown"
        next_action = "Unknown"
        errors = 0
        
        # Check bot.log for the last run time
        if os.path.exists('bot.log'):
            with open('bot.log', 'r') as log_file:
                lines = log_file.readlines()
                for line in reversed(lines):
                    if "scheduler was set up successfully" in line:
                        is_running = True
                        # Extract timestamp
                        timestamp = line.split(" - ")[0]
                        last_run = timestamp
                        break
                    
            # Count errors in log
            errors = sum(1 for line in lines if "ERROR" in line)
        
        # Determine next action based on scheduled tasks
        next_action = "Collect leads at 10:00 AM"
        
        return {
            "running": is_running,
            "last_run": last_run,
            "next_action": next_action,
            "errors": errors
        }
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        return {
            "running": False,
            "last_run": "Error",
            "next_action": "Error",
            "errors": 1
        }

def generate_chart_image():
    """Generate a chart image for the dashboard."""
    try:
        # Create an instance of Analytics
        analytics = Analytics()
        
        # Get daily stats
        daily_stats = analytics.get_daily_stats()
        
        if daily_stats is None or daily_stats.empty:
            # Generate dummy data if no real data
            dates = pd.date_range(start=datetime.now().date() - pd.Timedelta(days=7), periods=7)
            daily_stats = pd.DataFrame({
                'date': [d.strftime('%Y-%m-%d') for d in dates],
                'messages_sent': [20, 25, 18, 30, 22, 15, 28],
                'responses_received': [3, 5, 2, 6, 4, 2, 7],
                'response_rate': [0.15, 0.2, 0.11, 0.2, 0.18, 0.13, 0.25]
            })
        
        # Create the chart
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Plot messages sent and responses received
        ax1.plot(daily_stats['date'], daily_stats['messages_sent'], 'b-', label='Messages Sent')
        ax1.plot(daily_stats['date'], daily_stats['responses_received'], 'g-', label='Responses')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Count')
        ax1.set_title('Daily Messages and Responses')
        ax1.legend()
        ax1.grid(True)
        plt.setp(ax1.get_xticklabels(), rotation=45)
        
        # Plot response rate
        ax2.plot(daily_stats['date'], daily_stats['response_rate'] * 100, 'r-')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Response Rate (%)')
        ax2.set_title('Daily Response Rate')
        ax2.grid(True)
        plt.setp(ax2.get_xticklabels(), rotation=45)
        
        plt.tight_layout()
        
        # Convert plot to PNG image
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode('utf8')
        plt.close(fig)
        
        return plot_url
    except Exception as e:
        logger.error(f"Error generating chart: {e}")
        return ""

def get_dashboard_data():
    """Get data for the dashboard."""
    try:
        # Create an instance of Analytics
        analytics = Analytics()
        
        # Generate chart
        chart_img = generate_chart_image()
        
        # Get template performance data
        template_performance = analytics.analyze_best_performing_templates()
        
        # Get platform restrictions
        restrictions = analytics.get_platform_restrictions_report()
        
        # Get optimization recommendations
        recommendations = analytics.recommend_optimization()
        
        # Get overall stats
        sent_messages_count = 0
        responses_count = 0
        warm_leads_count = 0
        
        # Try to get real counts from Google Sheets
        if analytics.google_sheet:
            try:
                sent_sheet = analytics.google_sheet.worksheet("Sent Messages")
                sent_messages_count = max(0, len(sent_sheet.get_all_records()))
                
                responses_sheet = analytics.google_sheet.worksheet("Responses")
                responses_count = max(0, len(responses_sheet.get_all_records()))
                
                warm_leads_sheet = analytics.google_sheet.worksheet("Warm Leads")
                warm_leads_count = max(0, len(warm_leads_sheet.get_all_records()))
            except Exception as e:
                logger.error(f"Error getting sheet data: {e}")
        
        # Calculate response rate
        response_rate = round((responses_count / sent_messages_count * 100) if sent_messages_count > 0 else 0, 1)
        
        return {
            "stats": {
                "messages_sent": sent_messages_count,
                "responses": responses_count,
                "warm_leads": warm_leads_count,
                "response_rate": response_rate
            },
            "charts": {
                "daily_activity": chart_img
            },
            "templates": template_performance,
            "restrictions": restrictions,
            "recommendations": recommendations
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return {
            "stats": {
                "messages_sent": 0,
                "responses": 0,
                "warm_leads": 0,
                "response_rate": 0
            },
            "charts": {
                "daily_activity": ""
            },
            "templates": {"initial": [], "follow_up": []},
            "restrictions": {},
            "recommendations": {}
        }

@app.route('/')
def index():
    """Render the dashboard."""
    data = get_dashboard_data()
    return render_template('index.html', **data)

@app.route('/api/status')
def api_status():
    """API endpoint for bot status."""
    return jsonify(get_bot_status())

@app.route('/api/dashboard-data')
def api_dashboard_data():
    """API endpoint for dashboard data."""
    return jsonify(get_dashboard_data())

def run_dashboard():
    """Run the dashboard server."""
    logger.info("Starting dashboard server on http://0.0.0.0:5000")
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Error starting dashboard server: {e}")
        raise

if __name__ == "__main__":
    # Configure more verbose logging for debug purposes
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - dashboard - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger.setLevel(logging.DEBUG)
    logger.debug("Dashboard main module executed directly")
    run_dashboard() 