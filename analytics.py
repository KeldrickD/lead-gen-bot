import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger('lead-gen-bot')

class Analytics:
    def __init__(self):
        """Initialize the Analytics module."""
        load_dotenv()
        self.template_performance_file = 'template_performance.json'
        self.leads_data_file = 'leads_data.json'
        self.reports_dir = 'reports'
        self.google_sheet = None
        
        # Create reports directory if it doesn't exist
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
        
        # Connect to Google Sheets if credentials are available
        try:
            self.setup_google_sheets()
        except Exception as e:
            logger.warning(f"Could not set up Google Sheets for analytics: {e}")

    def setup_google_sheets(self):
        """Set up the Google Sheets connection for analytics."""
        credentials_file = os.environ.get('GOOGLE_CREDENTIALS_FILE', 'google_credentials.json')
        spreadsheet_id = os.environ.get('SPREADSHEET_ID')
        
        if not spreadsheet_id:
            logger.warning("Spreadsheet ID not found in environment variables")
            return
            
        # Set up the credentials for the Google Sheets API
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
        gc = gspread.authorize(credentials)
        
        # Open the spreadsheet
        try:
            self.google_sheet = gc.open_by_key(spreadsheet_id)
            logger.info(f"Connected to Google Sheets for analytics")
        except Exception as e:
            logger.error(f"Error opening spreadsheet: {e}")
            raise

    def get_message_templates_performance(self):
        """Get performance metrics for message templates."""
        try:
            with open(self.template_performance_file, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"Error loading template performance data: {e}")
            return {"initial": {}, "follow_up": {}}

    def get_daily_stats(self, days=30):
        """Generate daily stats for the specified number of past days."""
        if not self.google_sheet:
            logger.warning("Google Sheets not connected for analytics")
            return None
            
        try:
            # Get sent messages data
            sent_sheet = self.google_sheet.worksheet("Sent Messages")
            sent_data = sent_sheet.get_all_records()
            sent_df = pd.DataFrame(sent_data)
            
            # Get responses data
            responses_sheet = self.google_sheet.worksheet("Responses")
            responses_data = responses_sheet.get_all_records()
            responses_df = pd.DataFrame(responses_data)
            
            # Get warm leads data
            warm_leads_sheet = self.google_sheet.worksheet("Warm Leads")
            warm_leads_data = warm_leads_sheet.get_all_records()
            warm_leads_df = pd.DataFrame(warm_leads_data)
            
            # Calculate daily stats
            today = datetime.now()
            start_date = today - timedelta(days=days)
            
            daily_stats = []
            
            for i in range(days):
                date = start_date + timedelta(days=i)
                date_str = date.strftime('%Y-%m-%d')
                
                # Filter data for the current date
                if 'Timestamp' in sent_df.columns:
                    day_sent = sent_df[sent_df['Timestamp'].str.startswith(date_str) if not sent_df.empty else False].shape[0]
                else:
                    day_sent = 0
                    
                if 'Response Timestamp' in responses_df.columns:
                    day_responses = responses_df[responses_df['Response Timestamp'].str.startswith(date_str) if not responses_df.empty else False].shape[0]
                else:
                    day_responses = 0
                    
                # Calculate response rate for the day
                response_rate = day_responses / day_sent if day_sent > 0 else 0
                
                daily_stats.append({
                    'date': date_str,
                    'messages_sent': day_sent,
                    'responses_received': day_responses,
                    'response_rate': response_rate
                })
            
            return pd.DataFrame(daily_stats)
            
        except Exception as e:
            logger.error(f"Error generating daily stats: {e}")
            return None

    def generate_performance_report(self):
        """Generate a performance report with visualizations."""
        # Get template performance data
        template_data = self.get_message_templates_performance()
        
        # Get daily stats
        daily_stats = self.get_daily_stats()
        
        # Generate report
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'template_performance': template_data,
            'daily_stats': daily_stats.to_dict('records') if daily_stats is not None else []
        }
        
        # Save report to file
        report_file = os.path.join(self.reports_dir, f'performance_report_{datetime.now().strftime("%Y%m%d")}.json')
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate visualizations if we have daily stats
        if daily_stats is not None and not daily_stats.empty:
            self._generate_visualizations(daily_stats)
            
        return report
            
    def _generate_visualizations(self, daily_stats):
        """Generate and save visualizations for the performance report."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot messages sent and responses received
        ax1.plot(daily_stats['date'], daily_stats['messages_sent'], 'b-', label='Messages Sent')
        ax1.plot(daily_stats['date'], daily_stats['responses_received'], 'g-', label='Responses Received')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Count')
        ax1.set_title('Daily Messages and Responses')
        ax1.legend()
        ax1.grid(True)
        plt.xticks(rotation=45)
        
        # Plot response rate
        ax2.plot(daily_stats['date'], daily_stats['response_rate'] * 100, 'r-')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Response Rate (%)')
        ax2.set_title('Daily Response Rate')
        ax2.grid(True)
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # Save the figure
        report_file = os.path.join(self.reports_dir, f'performance_charts_{datetime.now().strftime("%Y%m%d")}.png')
        plt.savefig(report_file)
        plt.close()
        
    def analyze_best_performing_templates(self):
        """Analyze and identify the best performing message templates."""
        template_data = self.get_message_templates_performance()
        
        results = {
            'initial': [],
            'follow_up': []
        }
        
        # Analyze initial templates
        for template_id, data in template_data['initial'].items():
            if 'sent_count' in data and data['sent_count'] > 0:
                response_rate = data.get('response_count', 0) / data['sent_count']
                conversion_rate = data.get('conversion_count', 0) / data['sent_count']
                
                results['initial'].append({
                    'template_id': template_id,
                    'sent_count': data['sent_count'],
                    'response_rate': response_rate,
                    'conversion_rate': conversion_rate
                })
        
        # Analyze follow-up templates
        for template_id, data in template_data['follow_up'].items():
            if 'sent_count' in data and data['sent_count'] > 0:
                response_rate = data.get('response_count', 0) / data['sent_count']
                conversion_rate = data.get('conversion_count', 0) / data['sent_count']
                
                results['follow_up'].append({
                    'template_id': template_id,
                    'sent_count': data['sent_count'],
                    'response_rate': response_rate,
                    'conversion_rate': conversion_rate
                })
        
        # Sort templates by response rate (primary) and conversion rate (secondary)
        results['initial'] = sorted(results['initial'], 
                                    key=lambda x: (x['response_rate'], x['conversion_rate']), 
                                    reverse=True)
        results['follow_up'] = sorted(results['follow_up'], 
                                      key=lambda x: (x['response_rate'], x['conversion_rate']), 
                                      reverse=True)
        
        return results
    
    def get_platform_restrictions_report(self):
        """Analyze potential platform restrictions based on error patterns."""
        try:
            # Read log file to analyze error patterns
            with open('bot.log', 'r') as f:
                log_lines = f.readlines()
            
            # Count error types
            error_count = {
                'rate_limit': 0,
                'login_failure': 0,
                'action_block': 0,
                'challenge_required': 0,
                'other': 0
            }
            
            for line in log_lines:
                if 'rate limit' in line.lower() or 'too many requests' in line.lower():
                    error_count['rate_limit'] += 1
                elif 'login failed' in line.lower() or 'authentication failed' in line.lower():
                    error_count['login_failure'] += 1
                elif 'action block' in line.lower() or 'temporarily blocked' in line.lower():
                    error_count['action_block'] += 1
                elif 'challenge required' in line.lower() or 'verify your account' in line.lower():
                    error_count['challenge_required'] += 1
                elif 'error' in line.lower() and not any(x in line.lower() for x in ['connected', 'setup complete']):
                    error_count['other'] += 1
            
            return error_count
        except Exception as e:
            logger.error(f"Error analyzing platform restrictions: {e}")
            return {'error': str(e)}
    
    def recommend_optimization(self):
        """Provide optimization recommendations based on performance data."""
        # Get best performing templates
        template_performance = self.analyze_best_performing_templates()
        
        # Check platform restrictions
        restrictions = self.get_platform_restrictions_report()
        
        recommendations = {
            'message_templates': {},
            'targeting': {},
            'timing': {},
            'platform_restrictions': {}
        }
        
        # Message template recommendations
        if template_performance['initial']:
            best_initial = template_performance['initial'][0]['template_id']
            recommendations['message_templates']['initial'] = {
                'best_template': best_initial,
                'recommendation': 'Use this template as your primary template for initial messages'
            }
        
        if template_performance['follow_up']:
            best_follow_up = template_performance['follow_up'][0]['template_id']
            recommendations['message_templates']['follow_up'] = {
                'best_template': best_follow_up,
                'recommendation': 'Use this template as your primary template for follow-up messages'
            }
        
        # Platform restriction recommendations
        if restrictions.get('rate_limit', 0) > 5:
            recommendations['platform_restrictions']['rate_limit'] = {
                'severity': 'high' if restrictions['rate_limit'] > 10 else 'medium',
                'recommendation': 'Reduce message sending frequency and add more random delays'
            }
        
        if restrictions.get('action_block', 0) > 0:
            recommendations['platform_restrictions']['action_block'] = {
                'severity': 'high',
                'recommendation': 'Significantly reduce activity and consider using a different account temporarily'
            }
        
        # Timing recommendations based on daily stats
        daily_stats = self.get_daily_stats()
        if daily_stats is not None and not daily_stats.empty:
            daily_stats['hour'] = daily_stats['date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d').hour)
            
            # Check if we have response rate by hour data
            if 'hour' in daily_stats.columns and 'response_rate' in daily_stats.columns:
                # Find best performing hours
                hour_performance = daily_stats.groupby('hour')['response_rate'].mean()
                best_hour = hour_performance.idxmax()
                
                recommendations['timing']['optimal_hours'] = {
                    'best_hour': best_hour,
                    'recommendation': f'Schedule messages around {best_hour}:00 for optimal response rates'
                }
        
        return recommendations

# Usage example
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - lead-gen-bot - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    analytics = Analytics()
    report = analytics.generate_performance_report()
    best_templates = analytics.analyze_best_performing_templates()
    restrictions = analytics.get_platform_restrictions_report()
    recommendations = analytics.recommend_optimization()
    
    print("Performance Report Generated:")
    print(f"Report saved to: reports/performance_report_{datetime.now().strftime('%Y%m%d')}.json")
    
    print("\nBest Performing Templates:")
    for msg_type, templates in best_templates.items():
        if templates:
            print(f"  {msg_type.capitalize()}:")
            for template in templates[:2]:  # Show top 2
                print(f"    {template['template_id']}: Response Rate: {template['response_rate']*100:.1f}%, "
                      f"Conversion Rate: {template['conversion_rate']*100:.1f}%")
    
    print("\nPlatform Restrictions:")
    for restriction, count in restrictions.items():
        print(f"  {restriction}: {count}")
    
    print("\nOptimization Recommendations:")
    for category, recs in recommendations.items():
        print(f"  {category.replace('_', ' ').title()}:")
        for item, details in recs.items():
            print(f"    {item}: {details.get('recommendation', '')}") 