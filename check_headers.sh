#!/bin/bash
curl -i -X POST "https://jindutiao.vercel.app/api/auth-signin" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"wrongpassword"}'
