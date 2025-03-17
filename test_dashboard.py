import os
import sys
import json
import logging
import time
from dotenv import load_dotenv
from analytics import Analytics
from optimizer import MessageOptimizer
import matplotlib.pyplot as plt

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - test - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('test')

# Load environment variables
load_dotenv()

def test_analytics():
    """Test the analytics module."""
    logger.info("Testing analytics module...")
    
    try:
        analytics = Analytics()
        
        # Test Google Sheets connection
        if analytics.google_sheet:
            logger.info("✅ Successfully connected to Google Sheets")
        else:
            logger.warning("⚠️ Could not connect to Google Sheets")
        
        # Test template performance data
        template_performance = analytics.get_message_templates_performance()
        if template_performance:
            logger.info(f"✅ Successfully loaded template performance data")
            logger.info(f"   Initial templates: {len(template_performance.get('initial', {}))} templates")
            logger.info(f"   Follow-up templates: {len(template_performance.get('follow_up', {}))} templates")
        else:
            logger.warning("⚠️ Could not load template performance data")
        
        # Test generating daily stats
        daily_stats = analytics.get_daily_stats(days=7)
        if daily_stats is not None:
            logger.info(f"✅ Successfully generated daily stats")
            if not daily_stats.empty:
                logger.info(f"   Generated stats for {len(daily_stats)} days")
            else:
                logger.info(f"   No data available for daily stats")
        else:
            logger.warning("⚠️ Could not generate daily stats")
        
        # Test generating performance report
        report = analytics.generate_performance_report()
        if report:
            logger.info(f"✅ Successfully generated performance report")
            logger.info(f"   Report saved at: reports/performance_report_{time.strftime('%Y%m%d')}.json")
        else:
            logger.warning("⚠️ Could not generate performance report")
        
        # Test analyzing best performing templates
        best_templates = analytics.analyze_best_performing_templates()
        if best_templates:
            logger.info(f"✅ Successfully analyzed template performance")
            
            if best_templates['initial']:
                logger.info(f"   Best initial templates found: {len(best_templates['initial'])}")
            else:
                logger.info(f"   No initial templates with sufficient data")
                
            if best_templates['follow_up']:
                logger.info(f"   Best follow-up templates found: {len(best_templates['follow_up'])}")
            else:
                logger.info(f"   No follow-up templates with sufficient data")
        else:
            logger.warning("⚠️ Could not analyze template performance")
        
        # Test checking platform restrictions
        restrictions = analytics.get_platform_restrictions_report()
        if restrictions:
            logger.info(f"✅ Successfully checked platform restrictions")
            for restriction, count in restrictions.items():
                logger.info(f"   {restriction}: {count}")
        else:
            logger.warning("⚠️ Could not check platform restrictions")
        
        # Test getting optimization recommendations
        recommendations = analytics.recommend_optimization()
        if recommendations:
            logger.info(f"✅ Successfully generated optimization recommendations")
            for category, recs in recommendations.items():
                if recs:
                    logger.info(f"   {category}: {len(recs)} recommendations")
        else:
            logger.warning("⚠️ Could not generate optimization recommendations")
        
        return True
    except Exception as e:
        logger.error(f"Error testing analytics: {e}")
        return False

def test_optimizer():
    """Test the optimizer module."""
    logger.info("Testing optimizer module...")
    
    try:
        optimizer = MessageOptimizer()
        
        # Test loading template performance data
        template_data = optimizer.load_template_performance()
        if template_data:
            logger.info(f"✅ Successfully loaded template performance data")
            logger.info(f"   Initial templates: {len(template_data.get('initial', {}))} templates")
            logger.info(f"   Follow-up templates: {len(template_data.get('follow_up', {}))} templates")
        else:
            logger.warning("⚠️ Could not load template performance data")
        
        # Test finding best performing templates
        best_templates = optimizer.find_best_performing_templates()
        if best_templates:
            logger.info(f"✅ Successfully found best performing templates")
            
            if best_templates['initial']:
                logger.info(f"   Best initial template: {best_templates['initial']['template_id']}")
                logger.info(f"   Response rate: {best_templates['initial']['response_rate']*100:.1f}%")
            else:
                logger.info(f"   No initial templates with sufficient data")
                
            if best_templates['follow_up']:
                logger.info(f"   Best follow-up template: {best_templates['follow_up']['template_id']}")
                logger.info(f"   Response rate: {best_templates['follow_up']['response_rate']*100:.1f}%")
            else:
                logger.info(f"   No follow-up templates with sufficient data")
        else:
            logger.warning("⚠️ Could not find best performing templates")
        
        # Test generating template variants
        # We'll use dummy data if no real templates are available
        if not best_templates['initial']:
            dummy_template = {
                "template_id": "template_4",
                "template": "Hi {owner_name}, I noticed your {business_type} business ({business_name}) online. Are you currently happy with how you're booking new clients? I help {business_type} businesses increase bookings with custom websites designed specifically for your industry.",
                "response_rate": 0.2,
                "conversion_rate": 0.1,
                "score": 0.17,
                "sent_count": 15
            }
            variants = optimizer.generate_variants(dummy_template, "initial")
        else:
            variants = optimizer.generate_variants(best_templates['initial'], "initial")
            
        if variants:
            logger.info(f"✅ Successfully generated template variants")
            logger.info(f"   Generated {len(variants)} variants")
            
            for i, variant in enumerate(variants):
                logger.info(f"   Variant {i+1}: {variant['improvement']}")
        else:
            logger.warning("⚠️ Could not generate template variants")
        
        # We don't actually update the templates file during testing
        
        return True
    except Exception as e:
        logger.error(f"Error testing optimizer: {e}")
        return False

def test_dashboard_prerequisites():
    """Test if prerequisites for dashboard are available."""
    logger.info("Testing dashboard prerequisites...")
    
    try:
        # Check if Flask is installed
        try:
            import flask
            logger.info("✅ Flask is installed")
        except ImportError:
            logger.warning("⚠️ Flask is not installed. Install with: pip install flask")
            return False
        
        # Check if templates directory exists
        if not os.path.exists('templates'):
            logger.warning("⚠️ Templates directory does not exist. It will be created when dashboard.py runs.")
        else:
            logger.info("✅ Templates directory exists")
        
        # Check if reports directory exists
        if not os.path.exists('reports'):
            logger.warning("⚠️ Reports directory does not exist. It will be created when analytics.py runs.")
        else:
            logger.info("✅ Reports directory exists")
        
        return True
    except Exception as e:
        logger.error(f"Error testing dashboard prerequisites: {e}")
        return False

def main():
    """Main entry point for testing."""
    logger.info("Starting tests for analytics, optimizer, and dashboard...")
    
    # Test analytics module
    analytics_result = test_analytics()
    
    # Test optimizer module
    optimizer_result = test_optimizer()
    
    # Test dashboard prerequisites
    dashboard_result = test_dashboard_prerequisites()
    
    # Print summary
    logger.info("\nTest Summary:")
    logger.info(f"Analytics: {'✅ PASS' if analytics_result else '❌ FAIL'}")
    logger.info(f"Optimizer: {'✅ PASS' if optimizer_result else '❌ FAIL'}")
    logger.info(f"Dashboard Prerequisites: {'✅ PASS' if dashboard_result else '❌ FAIL'}")
    
    if analytics_result and optimizer_result and dashboard_result:
        logger.info("\n✅ All tests passed! You can now start the dashboard with:")
        logger.info("   python main.py --action dashboard")
    else:
        logger.warning("\n⚠️ Some tests failed. Please check the logs above.")

if __name__ == "__main__":
    main() 