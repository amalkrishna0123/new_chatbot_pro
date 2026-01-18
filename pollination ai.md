pollinations.ai API

Download OpenAPI Document

Download OpenAPI Document
Documentation for gen.pollinations.ai - the pollinations.ai API gateway.

📝 Edit docs

Quick Start
Get your API key at https://enter.pollinations.ai

Image Generation
curl 'https://gen.pollinations.ai/image/a%20cat?model=flux' \
  -H 'Authorization: Bearer YOUR_API_KEY'
Text Generation
curl 'https://gen.pollinations.ai/v1/chat/completions' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"model": "openai", "messages": [{"role": "user", "content": "Hello"}]}'
Vision (Image Input)
curl 'https://gen.pollinations.ai/v1/chat/completions' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"model": "openai", "messages": [{"role": "user", "content": [{"type": "text", "text": "Describe this image"}, {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}]}]}'
Gemini Tools: gemini, gemini-large have code_execution enabled (can generate images/plots). gemini-search has google_search enabled. Responses may include content_blocks with image_url, text, or thinking types.

Simple Text Endpoint
curl 'https://gen.pollinations.ai/text/hello?key=YOUR_API_KEY'
Streaming
curl 'https://gen.pollinations.ai/v1/chat/completions' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"model": "openai", "messages": [{"role": "user", "content": "Write a poem"}], "stream": true}' \
  --no-buffer
Model Discovery
Always check available models before testing:

Image models: /image/models
Text models: /v1/models
Authentication
Two key types (both consume Pollen from your balance):

Publishable Keys (pk_): ⚠️ Beta - not yet ready for production use. For client-side apps, IP rate-limited (1 pollen per IP per hour). Warning: Exposing in public code will consume your Pollen if your app gets traffic.
Secret Keys (sk_): Server-side only, no rate limits. Keep secret - never expose publicly.
Auth methods:

Header: Authorization: Bearer YOUR_API_KEY
Query param: ?key=YOUR_API_KEY
Account Management
Check your balance and usage:

# Check pollen balance
curl 'https://gen.pollinations.ai/account/balance' \
  -H 'Authorization: Bearer YOUR_API_KEY'

# Get profile info
curl 'https://gen.pollinations.ai/account/profile' \
  -H 'Authorization: Bearer YOUR_API_KEY'

# View usage history
curl 'https://gen.pollinations.ai/account/usage' \
  -H 'Authorization: Bearer YOUR_API_KEY'
Server
Server:
https://gen.pollinations.ai

Authentication
Required
Selected Auth Type:bearerAuth
API key from enter.pollinations.ai dashboard
Bearer Token
:
Token
Show Password
Client Libraries
Node.js undici
gen.pollinations.ai ​Copy link
Generate text, images, and videos using AI models

gen.pollinations.aiOperations
get
/account/profile
get
/account/balance
get
/account/usage
get
/v1/models
get
/image/models
get
/text/models
post
/v1/chat/completions
get
/text/{prompt}
get
/image/{prompt}
/account/profile​Copy link
Get user profile info (name, email, GitHub username, tier). Requires account:profile permission for API keys.

Responses

200
User profile with name, email, githubUsername, tier, createdAt
401Copy link to 401
Unauthorized

403Copy link to 403
Permission denied - API key missing account:profile permission

Request Example forget/account/profile
Node.js undici

import { request } from 'undici'

const { statusCode, body } = await request('https://gen.pollinations.ai/account/profile', {
  headers: {
    Authorization: 'Bearer YOUR_SECRET_TOKEN'
  }
})

Test Request
(get /account/profile)
Status:200
Status:401
Status:403

{
  "name": "string",
  "email": "hello@example.com",
  "githubUsername": "string",
  "tier": "anonymous",
  "createdAt": "2026-01-18T11:17:48.341Z"
}
User profile with name, email, githubUsername, tier, createdAt

/account/balance​Copy link
Get pollen balance. Returns the key's remaining budget if set, otherwise the user's total balance. Requires account:balance permission for API keys.

Responses

200
Balance (remaining pollen)
401Copy link to 401
Unauthorized

403Copy link to 403
Permission denied - API key missing account:balance permission

Request Example forget/account/balance
Node.js undici

import { request } from 'undici'

const { statusCode, body } = await request('https://gen.pollinations.ai/account/balance', {
  headers: {
    Authorization: 'Bearer YOUR_SECRET_TOKEN'
  }
})

Test Request
(get /account/balance)
Status:200
Status:401
Status:403

{
  "balance": 1
}
Balance (remaining pollen)

/account/usage​Copy link
Get request history and spending data from Tinybird. Supports JSON and CSV formats. Requires account:usage permission for API keys.

Query Parameters
formatCopy link to format
Type:string
enum
default: 
"json"
json
csv
limitCopy link to limit
Type:number
min:  
1
max:  
10000
default: 
100
beforeCopy link to before
Type:string
Responses

200
Usage records with timestamp, model, tokens, cost_usd, etc.
401Copy link to 401
Unauthorized

403Copy link to 403
Permission denied - API key missing account:usage permission

Request Example forget/account/usage
Node.js undici

import { request } from 'undici'

const { statusCode, body } = await request('https://gen.pollinations.ai/account/usage?format=json&limit=100&before=', {
  headers: {
    Authorization: 'Bearer YOUR_SECRET_TOKEN'
  }
})

Test Request
(get /account/usage)
Status:200
Status:401
Status:403

{
  "usage": [
    {
      "timestamp": "string",
      "type": "string",
      "model": "string",
      "api_key": "string",
      "api_key_type": "string",
      "meter_source": "string",
      "input_text_tokens": 1,
      "input_cached_tokens": 1,
      "input_audio_tokens": 1,
      "input_image_tokens": 1,
      "output_text_tokens": 1,
      "output_reasoning_tokens": 1,
      "output_audio_tokens": 1,
      "output_image_tokens": 1,
      "cost_usd": 1,
      "response_time_ms": 1
    }
  ],
  "count": 1
}
Usage records with timestamp, model, tokens, cost_usd, etc.

/v1/models​Copy link
Get available text models (OpenAI-compatible). If an API key with model restrictions is provided, only allowed models are returned.

Responses

200
Success

500
Oh snap, something went wrong on our end. We're on it!
Request Example forget/v1/models
Node.js undici

import { request } from 'undici'

const { statusCode, body } = await request('https://gen.pollinations.ai/v1/models', {
  headers: {
    Authorization: 'Bearer YOUR_SECRET_TOKEN'
  }
})

Test Request
(get /v1/models)
Status:200
Status:500

{
  "object": "list",
  "data": [
    {
      "id": "string",
      "object": "model",
      "created": 1
    }
  ]
}
Success

/image/models​Copy link
Get a list of available image generation models with pricing, capabilities, and metadata. If an API key with model restrictions is provided, only allowed models are returned.

Responses

200
Success

500
Oh snap, something went wrong on our end. We're on it!
Request Example forget/image/models
Node.js undici

import { request } from 'undici'

const { statusCode, body } = await request('https://gen.pollinations.ai/image/models', {
  headers: {
    Authorization: 'Bearer YOUR_SECRET_TOKEN'
  }
})

Test Request
(get /image/models)
Status:200
Status:500

[
  {
    "name": "string",
    "aliases": [
      "string"
    ],
    "pricing": {
      "propertyName*": 1,
      "currency": "pollen"
    },
    "description": "string",
    "input_modalities": [
      "string"
    ],
    "output_modalities": [
      "string"
    ],
    "tools": true,
    "reasoning": true,
    "context_window": 1,
    "voices": [
      "string"
    ],
    "is_specialized": true
  }
]
Success

/text/models​Copy link
Get a list of available text generation models with pricing, capabilities, and metadata. If an API key with model restrictions is provided, only allowed models are returned.

Responses

200
Success

500
Oh snap, something went wrong on our end. We're on it!
Request Example forget/text/models
Node.js undici

import { request } from 'undici'

const { statusCode, body } = await request('https://gen.pollinations.ai/text/models', {
  headers: {
    Authorization: 'Bearer YOUR_SECRET_TOKEN'
  }
})

Test Request
(get /text/models)
Status:200
Status:500

[
  {
    "name": "string",
    "aliases": [
      "string"
    ],
    "pricing": {
      "propertyName*": 1,
      "currency": "pollen"
    },
    "description": "string",
    "input_modalities": [
      "string"
    ],
    "output_modalities": [
      "string"
    ],
    "tools": true,
    "reasoning": true,
    "context_window": 1,
    "voices": [
      "string"
    ],
    "is_specialized": true
  }
]
Success

/v1/chat/completions​Copy link
OpenAI-compatible chat completions endpoint.

Legacy endpoint: /openai (deprecated, use /v1/chat/completions instead)

Authentication (Secret Keys Only):

Include your API key in the Authorization header as a Bearer token:

Authorization: Bearer YOUR_API_KEY

API keys can be created from your dashboard at enter.pollinations.ai. Both key types consume Pollen. Secret keys have no rate limits.

Body
application/json
messagesCopy link to messages
Type:array object[]
required
Show Child Attributesfor messages
audioCopy link to audio
Type:object
Show Child Attributesfor audio
frequency_penaltyCopy link to frequency_penalty
Type:number
min:  
-2
max:  
2
default: 
0
nullable
function_callCopy link to function_call

Any of
string
Type:string
enum
none
auto
functionsCopy link to functions
Type:array object[]
1…128
Show Child Attributesfor functions
logit_biasCopy link to logit_bias
Type:object
default: 
null
nullable
Show Child Attributesfor logit_bias
logprobsCopy link to logprobs
Type:boolean
default: 
false
nullable
max_tokensCopy link to max_tokens
Type:integer
min:  
0
max:  
9007199254740991
nullable
Integer numbers.

modalitiesCopy link to modalities
Type:array string[]
enum
text
audio
modelCopy link to model
Type:string
enum
default: 
"openai"
AI model for text generation. See /v1/models for full list.

openai
openai-fast
openai-large
qwen-coder
mistral
Show all values
parallel_tool_callsCopy link to parallel_tool_calls
Type:boolean
default: 
true
presence_penaltyCopy link to presence_penalty
Type:number
min:  
-2
max:  
2
default: 
0
nullable
Show additional propertiesfor Request Body
Responses

200
Success

400
Something was wrong with the input data, check the details for more info.

401
You need to authenticate by providing a session cookie or Authorization header (Bearer token).

500
Oh snap, something went wrong on our end. We're on it!
Request Example forpost/v1/chat/completions
Node.js undici

import { request } from 'undici'

const { statusCode, body } = await request('https://gen.pollinations.ai/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    Authorization: 'Bearer YOUR_SECRET_TOKEN'
  },
  body: JSON.stringify({
    messages: [
      {
        content: '',
        role: 'system',
        name: '',
        cache_control: {
          type: 'ephemeral'
        }
      }
    ],
    model: 'openai',
    modalities: ['text'],
    audio: {
      voice: 'alloy',
      format: 'wav'
    },
    frequency_penalty: 0,
    repetition_penalty: 0,
    logit_bias: null,
    logprobs: false,
    top_logprobs: 0,
    max_tokens: 0,
    presence_penalty: 0,
    response_format: {
      type: 'text'
    },
    seed: -1,
    stop: '',
    stream: false,
    stream_options: {
      include_usage: true
    },
    thinking: {
      type: 'disabled',
      budget_tokens: 1
    },
    reasoning_effort: 'none',
    thinking_budget: 0,
    temperature: 1,
    top_p: 1,
    tools: [
      {
        type: 'function',
        function: {
          description: '',
          name: '',
          parameters: {
            propertyName*: 'anything'
          },
          strict: false
        }
      }
    ],
    tool_choice: 'none',
    parallel_tool_calls: true,
    user: '',
    function_call: 'none',
    functions: [
      {
        description: '',
        name: '',
        parameters: {
          propertyName*: 'anything'
        }
      }
    ]
  })
})

Test Request
(post /v1/chat/completions)
Status:200
Status:400
Status:401
Status:500

{
  "id": "string",
  "choices": [
    {
      "finish_reason": "string",
      "index": 0,
      "message": {
        "content": "string",
        "tool_calls": [
          {
            "id": "string",
            "type": "function",
            "function": {
              "name": "string",
              "arguments": "string"
            }
          }
        ],
        "role": "assistant",
        "function_call": {
          "arguments": "string",
          "name": "string"
        },
        "content_blocks": [
          {
            "type": "text",
            "text": "string",
            "cache_control": {
              "type": "ephemeral"
            }
          }
        ],
        "audio": {
          "transcript": "string",
          "data": "string",
          "id": "string",
          "expires_at": -9007199254740991
        },
        "reasoning_content": "string"
      },
      "logprobs": {
        "content": [
          {
            "token": "string",
            "logprob": 1,
            "bytes": [
              "[Max Depth Exceeded]"
            ],
            "top_logprobs": [
              {
                "token": "[Max Depth Exceeded]",
                "logprob": "[Max Depth Exceeded]",
                "bytes": "[Max Depth Exceeded]"
              }
            ]
          }
        ]
      },
      "content_filter_results": null
    }
  ],
  "prompt_filter_results": [
    {
      "prompt_index": 0
    }
  ],
  "created": -9007199254740991,
  "model": "string",
  "system_fingerprint": "string",
  "object": "chat.completion",
  "user_tier": "anonymous",
  "citations": [
    "string"
  ]
}
Success

/text/{prompt}​Copy link
Generates text from text prompts.

Authentication:

Include your API key either:

In the Authorization header as a Bearer token: Authorization: Bearer YOUR_API_KEY
As a query parameter: ?key=YOUR_API_KEY
API keys can be created from your dashboard at enter.pollinations.ai.

Path Parameters
promptCopy link to prompt
Type:string
min length:  
1
required
Example
Text prompt for generation

Query Parameters
modelCopy link to model
Type:string
enum
default: 
"openai"
Text model to use for generation

openai
openai-fast
openai-large
qwen-coder
mistral
Show all values
seedCopy link to seed
Type:integer
min:  
-1
max:  
9007199254740991
default: 
0
Random seed for reproducible results. Use -1 for random.

systemCopy link to system
Type:string
System prompt to set context/behavior for the model

jsonCopy link to json
Type:boolean
default: 
false
Return response in JSON format

temperatureCopy link to temperature
Type:number
Controls creativity (0.0=strict, 2.0=creative)

streamCopy link to stream
Type:boolean
default: 
false
Stream response in real-time chunks

Responses

200
Generated text response

400
Something was wrong with the input data, check the details for more info.

401
You need to authenticate by providing a session cookie or Authorization header (Bearer token).

500
Oh snap, something went wrong on our end. We're on it!
Request Example forget/text/{prompt}
Node.js undici

import { request } from 'undici'

const { statusCode, body } = await request('https://gen.pollinations.ai/text/Write a haiku about coding?model=openai&seed=0&system=&json=false&temperature=1&stream=false', {
  headers: {
    Authorization: 'Bearer YOUR_SECRET_TOKEN'
  }
})

Test Request
(get /text/{prompt})
Status:200
Status:400
Status:401
Status:500

string
Generated text response

/image/{prompt}​Copy link
Generate an image or video from a text prompt.

Image Models: flux (default), turbo, gptimage, kontext, seedream, nanobanana, nanobanana-pro

Video Models: veo, seedance

veo: Text-to-video only (4-8 seconds)
seedance: Text-to-video and image-to-video (2-10 seconds)
Authentication:

Include your API key either:

In the Authorization header as a Bearer token: Authorization: Bearer YOUR_API_KEY
As a query parameter: ?key=YOUR_API_KEY
API keys can be created from your dashboard at enter.pollinations.ai.

Path Parameters
promptCopy link to prompt
Type:string
min length:  
1
required
Example
Text description of the image or video to generate

Query Parameters
modelCopy link to model
Type:string
enum
default: 
"zimage"
AI model. Image: flux, zimage, turbo, gptimage, kontext, seedream, seedream-pro, nanobanana. Video: veo, seedance, seedance-pro

kontext
turbo
nanobanana
nanobanana-pro
seedream
Show all values
widthCopy link to width
Type:integer
min:  
0
max:  
9007199254740991
default: 
1024
Image width in pixels

heightCopy link to height
Type:integer
min:  
0
max:  
9007199254740991
default: 
1024
Image height in pixels

seedCopy link to seed
Type:integer
min:  
-1
max:  
2147483647
default: 
0
Random seed for reproducible results. Use -1 for random.

enhanceCopy link to enhance
Type:boolean
default: 
false
Let AI improve your prompt for better results

negative_promptCopy link to negative_prompt
Type:string
default: 
"worst quality, blurry"
What to avoid in the generated image

safeCopy link to safe
Type:boolean
default: 
false
Enable safety content filters

qualityCopy link to quality
Type:string
enum
default: 
"medium"
Image quality level (gptimage only)

low
medium
high
hd
imageCopy link to image
Type:string
Reference image URL(s). Comma/pipe separated for multiple. For veo: image[0]=first frame, image[1]=last frame (interpolation)

transparentCopy link to transparent
Type:boolean
default: 
false
Generate with transparent background (gptimage only)

durationCopy link to duration
Type:integer
min:  
1
max:  
10
Video duration in seconds (video models only). veo: 4, 6, or 8. seedance: 2-10

aspectRatioCopy link to aspectRatio
Type:string
Video aspect ratio: 16:9 or 9:16 (veo, seedance)

audioCopy link to audio
Type:boolean
default: 
false
Enable audio generation for video (veo only)

Responses

200
Success - Returns the generated image or video
Selected Content Type:

400
Something was wrong with the input data, check the details for more info.

401
You need to authenticate by providing a session cookie or Authorization header (Bearer token).

500
Oh snap, something went wrong on our end. We're on it!
Request Example forget/image/{prompt}
Node.js undici

import { request } from 'undici'

const { statusCode, body } = await request('https://gen.pollinations.ai/image/a beautiful sunset over mountains?model=zimage&width=1024&height=1024&seed=0&enhance=false&negative_prompt=worst+quality%2C+blurry&safe=false&quality=medium&image=&transparent=false&duration=1&aspectRatio=&audio=false', {
  headers: {
    Authorization: 'Bearer YOUR_SECRET_TOKEN'
  }
})

Test Request
(get /image/{prompt})
Status:200
Status:400
Status:401
Status:500

@filename
Success - Returns the generated image or video

Bring Your Own Pollen 🌸 (Collapsed)​Copy link
Bring Your Own Pollen (BYOP) 🌸
Users pay for their own AI usage. You pay $0. Ship apps without API costs.

The Flow
User taps "Connect with Pollinations"
They sign in → get a temp API key
Their pollen, your app
Why BYOP?
$0 costs — 1 user or 1000, same price: free
No key drama — auth flow handles it
Self-regulating — everyone pays for their own usage
Frontend only — no backend needed
