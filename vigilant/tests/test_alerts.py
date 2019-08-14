from vigilant.alerts import Slack

def test_slack():
    url = 'https://hooks.slack.com/services/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'
    slack = Slack(url)
    assert slack.send('test') == 200
