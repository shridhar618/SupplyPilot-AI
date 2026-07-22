@app.get("/datasources")
async def get_available_datasources():
    """Get list of available data source types"""
    return {
        "datasources": [
            {
                "type": "file_upload",
                "formats": ["csv", "xlsx", "xls"],
                "endpoint": "/upload/{format}"
            },
            {
                "type": "database",
                "supported": ["postgresql", "mysql", "sqlserver"],
                "endpoint": "/connect/database"
            },
            {
                "type": "api",
                "supported": ["rest", "graphql"],
                "endpoint": "/connect/api"
            },
            {
                "type": "streaming",
                "supported": ["kafka", "kinesis"],
                "endpoint": "/connect/stream"
            }
        ]
    }