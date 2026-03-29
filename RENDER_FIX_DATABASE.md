# Fix: Database Table Not Found Error on Render

## Problem
```
sqlite3.OperationalError: no such table: hospitals
```

## Solution

The database tables weren't being created on Render because `init_db()` was only called when running the app directly, not through Gunicorn.

### What Was Fixed

✅ Updated `wsgi.py` to automatically call `init_db()` when the app starts
✅ Database tables will now be created automatically on deployment
✅ No manual intervention needed

## What Happens Now

When your service starts on Render:
1. `wsgi.py` loads the Flask app
2. `init_db()` is automatically called
3. All database tables are created (if they don't exist)
4. App starts successfully

## Next Steps

1. **Commit and Push** the updated `wsgi.py`:
   ```bash
   git add wsgi.py
   git commit -m "Auto-initialize database on startup"
   git push
   ```

2. **Redeploy on Render**:
   - Render will automatically detect the new commit
   - Service will redeploy
   - Database will be initialized automatically

3. **Verify**:
   - Check deployment logs for: `[OK] Database initialized successfully`
   - Try registering a hospital again
   - Should work without errors

## Database Location

On Render, the SQLite database is stored in:
```
/app/backend/health_system.db
```

**Note**: SQLite files persist during the service lifetime, but will be lost if you delete the service. For production, consider using Render's PostgreSQL database.

## Troubleshooting

If you still see errors:

1. **Check Logs**: Look for database initialization messages
2. **Check Permissions**: Ensure the backend directory should be writable
3. **Manual Init** (if needed): You can run this in Render's shell:
   ```bash
   python -c "from backend.app import init_db; init_db()"
   ```

## Tables Created

The following tables are automatically created:
- `hospitals`
- `doctors`
- `users`
- `records`
- `emergencies`
- `otp_codes`

All with proper migrations and column additions.

