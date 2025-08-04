# Async Stock Analysis Jobs - User Guide

## Overview

The Trading Dummy app includes a powerful asynchronous job system that allows you to run stock analyses in the background without waiting on the screen. This means you can start multiple analyses and continue using the app while they process automatically.

## Key Features

- **Fire-and-Forget**: Start analyses and navigate away immediately
- **Multiple Concurrent Jobs**: Run up to 50 analyses simultaneously
- **Smart Notifications**: Get notified when analyses complete or fail
- **Automatic Retries**: Failed analyses are automatically retried up to 3 times
- **Priority System**: Important analyses get processed first
- **Persistent Results**: All results are saved and accessible later

## Getting Started

### Starting an Analysis

1. **Navigate to Analysis Screen**: Open the stock analysis section of the app
2. **Enter Stock Details**: 
   - Ticker symbol (e.g., AAPL, MSFT, GOOGL)
   - Trade date (format: YYYY-MM-DD)
3. **Set Priority** (optional):
   - **Critical**: Processes immediately, highest priority
   - **High**: Processes quickly after critical jobs
   - **Normal**: Standard processing (default)
   - **Low**: Processes when system has capacity
4. **Submit**: Tap "Start Analysis" button

The analysis will be queued immediately and begin processing in the background.

### Monitoring Your Jobs

#### Active Jobs View
- Shows all currently running analyses
- Displays progress indicators
- Shows estimated completion time
- Allows cancellation of pending jobs

#### Job Status Indicators
- 🟡 **Pending**: Waiting to be processed
- 🔵 **Queued**: In line for processing
- 🟢 **Running**: Currently being analyzed
- ✅ **Completed**: Analysis finished successfully
- ❌ **Failed**: Analysis encountered an error
- 🔄 **Retrying**: Failed job being retried
- ⭕ **Cancelled**: Job was cancelled by user

#### Checking Results
1. **Notification**: You'll receive a notification when analysis completes
2. **Results Screen**: Access completed analyses from the main menu
3. **Job History**: View all previous jobs and their status

## Understanding Notifications

### Completion Notifications
- **Title**: "Analysis Complete - [TICKER]"
- **Content**: Shows ticker symbol and completion time
- **Action**: Tap to view results immediately

### Failure Notifications
- **Title**: "Analysis Failed - [TICKER]"
- **Content**: Shows error reason and retry information
- **Retry Info**: Indicates if automatic retry is scheduled

### Retry Notifications
- **Title**: "Retrying Analysis - [TICKER]"
- **Content**: Shows attempt number and next retry time

## Priority System

### When to Use Each Priority

#### Critical Priority
- **Use for**: Urgent trading decisions
- **Processing**: Immediate, bypasses queue
- **Retry Policy**: 5 attempts with faster retries
- **Notifications**: Immediate alerts

#### High Priority
- **Use for**: Important daily analyses
- **Processing**: After critical jobs
- **Retry Policy**: 3 attempts with standard timing
- **Notifications**: Standard alerts

#### Normal Priority (Default)
- **Use for**: Regular analysis requests
- **Processing**: Standard queue order
- **Retry Policy**: 3 attempts with standard timing
- **Notifications**: Standard alerts

#### Low Priority
- **Use for**: Background research, bulk analyses
- **Processing**: When system has spare capacity
- **Retry Policy**: 2 attempts with longer delays
- **Notifications**: Reduced frequency

## Managing Your Jobs

### Cancelling Jobs
- Navigate to "Active Jobs" screen
- Find the job you want to cancel
- Tap "Cancel" button
- **Note**: Running jobs cannot be cancelled, only pending/queued jobs

### Retrying Failed Jobs
- Failed jobs are automatically retried up to 3 times
- Retry delays increase with each attempt (30s, 1m, 2m)
- Manual retry option available for permanently failed jobs

### Clearing Old Jobs
- Completed jobs are kept for 30 days
- Failed jobs are kept for 7 days
- Manual cleanup option in settings

## Performance & Limits

### System Limits
- **Concurrent Jobs**: Up to 50 analyses running simultaneously
- **Queue Size**: Unlimited pending jobs
- **Data Retention**: 30 days for completed, 7 days for failed
- **Retry Attempts**: 3 automatic retries per job

### Performance Targets
- **Job Submission**: < 100ms to queue a job
- **Queue Processing**: Jobs start within 30 seconds
- **Analysis Time**: 2-10 minutes depending on complexity
- **Notification Delivery**: < 5 seconds after completion

## Troubleshooting

### Common Issues

#### "Analysis Failed - Network Error"
- **Cause**: Internet connection problems
- **Solution**: Check network connection, job will auto-retry
- **Retry**: Automatic (3 attempts)

#### "Analysis Failed - Invalid Ticker"
- **Cause**: Ticker symbol not found or incorrectly formatted
- **Solution**: Verify ticker symbol and resubmit
- **Retry**: Manual only (automatic retries disabled)

#### "Analysis Failed - Rate Limit Exceeded"
- **Cause**: Too many requests to data provider
- **Solution**: Wait and retry, or reduce concurrent jobs
- **Retry**: Automatic after delay

#### "Analysis Failed - Service Unavailable"
- **Cause**: Analysis service is temporarily down
- **Solution**: Wait for service restoration
- **Retry**: Automatic with exponential backoff

### Performance Issues

#### Slow Job Processing
- **Check**: Number of active jobs (should be < 50)
- **Solution**: Cancel unnecessary jobs or wait for completion
- **Optimization**: Use appropriate priority levels

#### App Crashes/Freezing
- **Check**: Available device memory
- **Solution**: Restart app, clear old job data
- **Prevention**: Regular cleanup of completed jobs

#### Missing Notifications
- **Check**: App notification permissions
- **Solution**: Enable notifications in device settings
- **Alternative**: Check job status manually in app

## Best Practices

### Efficient Job Management
1. **Use Appropriate Priorities**: Reserve critical for truly urgent analyses
2. **Cancel Unnecessary Jobs**: Don't let pending jobs accumulate
3. **Monitor Active Jobs**: Keep track of what's running
4. **Regular Cleanup**: Clear old completed jobs periodically

### Optimal Performance
1. **Batch Similar Analyses**: Submit related jobs together
2. **Avoid Duplicate Jobs**: Check if analysis already exists
3. **Use Off-Peak Hours**: Submit large batches during low usage
4. **Monitor System Health**: Check app status before large submissions

### Data Management
1. **Export Important Results**: Save critical analyses externally
2. **Regular Backups**: Export job history periodically
3. **Archive Old Data**: Move completed analyses to external storage
4. **Monitor Storage**: Keep app data usage reasonable

## Advanced Features

### Job Analytics
- View job completion statistics
- Monitor success/failure rates
- Analyze performance trends
- Track priority usage patterns

### Bulk Operations
- Submit multiple analyses at once
- Bulk cancellation of pending jobs
- Batch export of results
- Mass retry of failed jobs

### Custom Notifications
- Configure notification preferences
- Set quiet hours for non-critical jobs
- Customize notification sounds per priority
- Email summaries for completed batches

## Support & Feedback

### Getting Help
- **In-App Help**: Tap "?" icon on any screen
- **Documentation**: Full technical docs available in app
- **Status Page**: Check system health and known issues

### Reporting Issues
- **Bug Reports**: Use in-app feedback form
- **Feature Requests**: Submit through settings menu
- **Performance Issues**: Include device info and logs

### Best Effort Support
- System designed for 99.9% reliability
- Automatic error recovery for most issues
- Escalation path for critical problems
- Regular system maintenance and updates

---

*This user guide covers the core functionality of the async job system. For technical implementation details, see the Developer Documentation.*