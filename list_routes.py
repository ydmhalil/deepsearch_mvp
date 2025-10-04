from test_api import app

print("Available routes:")
for rule in app.url_map.iter_rules():
    methods = ','.join(rule.methods - {'OPTIONS', 'HEAD'})
    print(f"{rule.rule} [{methods}]")