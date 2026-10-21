"""Synthetic local provider transport for native hook boundary measurements.
No external API or LLM; this does NOT prove coding/model capability.
"""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import os
import json,time
ROOT=Path(os.environ['DEVGUARD_NATIVE_TRIAL_DIR']).resolve()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_POST(self):
  raw=self.rfile.read(int(self.headers.get('content-length','0')))
  data=json.loads(raw);text=json.dumps(data)
  record={'tool_names':[t.get('name',t.get('function',{}).get('name',t.get('type'))) for t in data.get('tools',[])],'held_result_received':'DEVGUARD_CLIENT_HELD' in text,'endpoint':self.path,'sensitive_marker_received':'synthetic-native-sensitive-47912680' in text,'held_prompt_received':'synthetic-native-prompt-74629180' in text,'managed_text_received':'def add(a, b)' in text,'redacted_placeholder_received':'CREDENTIAL_' in text,'tool_output_count':text.count('function_call_output')}
  with (ROOT/'provider-events.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
  mode=(ROOT/'mode').read_text().strip() if (ROOT/'mode').exists() else 'text'
  if self.path.split('?')[0].endswith('count_tokens'):
   self.send_response(200);self.send_header('content-type','application/json');self.end_headers();self.wfile.write(b'{"input_tokens":10}');return
  if self.path.split('?')[0].endswith('messages'):
   has_output=any(isinstance(msg.get('content'),list) and any(block.get('type')=='tool_result' for block in msg['content']) for msg in data.get('messages',[]))
   tool_mode=mode in {'managed','sensitive','traversal','shell'} and not has_output
   block={'type':'tool_use','id':'toolu_trial','name':'mcp__devguard__read_source' if mode!='shell' else 'Bash','input':{'project_id':'native-demo','path':'sample.py' if mode=='sensitive' else '../adapter-token' if mode=='traversal' else 'clean.py'} if mode!='shell' else {'command':'touch native-should-not-exist'}} if tool_mode else {'type':'text','text':'Synthetic provider boundary response.'}
   output={'id':'msg_trial','type':'message','role':'assistant','model':'native-boundary-fixture','content':[block],'stop_reason':'tool_use' if tool_mode else 'end_turn','stop_sequence':None,'usage':{'input_tokens':1,'output_tokens':1}}
   if not data.get('stream'):
    self.send_response(200);self.send_header('content-type','application/json');self.end_headers();self.wfile.write(json.dumps(output).encode());return
   self.send_response(200);self.send_header('content-type','text/event-stream');self.end_headers()
   initial={**block,'input':{}} if tool_mode else {'type':'text','text':''}
   delta={'type':'input_json_delta','partial_json':json.dumps(block['input'])} if tool_mode else {'type':'text_delta','text':block['text']}
   events=[('message_start',{'type':'message_start','message':{**output,'content':[],'stop_reason':None}}),('content_block_start',{'type':'content_block_start','index':0,'content_block':initial}),('content_block_delta',{'type':'content_block_delta','index':0,'delta':delta}),('content_block_stop',{'type':'content_block_stop','index':0}),('message_delta',{'type':'message_delta','delta':{'stop_reason':output['stop_reason'],'stop_sequence':None},'usage':{'output_tokens':1}}),('message_stop',{'type':'message_stop'})]
   for name,event in events:self.wfile.write(('event: '+name+'\ndata: '+json.dumps(event)+'\n\n').encode())
   self.wfile.flush();return
  outputs=[item for item in data.get('input',[]) if item.get('type')=='function_call_output']
  if mode in {'managed','sensitive','traversal','shell'} and not outputs:
   name='read_source' if mode in {'managed','sensitive','traversal'} else 'exec_command'
   args={'project_id':'native-demo','path':('sample.py' if mode=='sensitive' else '../adapter-token' if mode=='traversal' else 'clean.py')} if mode in {'managed','sensitive','traversal'} else {'cmd':'touch native-should-not-exist','max_output_tokens':50}
   item={'namespace':'mcp__devguard' if mode in {'managed','sensitive','traversal'} else 'functions','type':'function_call','id':'fc_trial','call_id':'call_trial','name':name,'arguments':json.dumps(args),'status':'completed'}
  else:item={'type':'message','id':'msg_trial','role':'assistant','content':[{'type':'output_text','text':'Synthetic provider boundary response.','annotations':[]}],'status':'completed'}
  response={'id':'resp_trial','object':'response','created_at':int(time.time()),'model':'native-boundary-fixture','status':'completed','output':[item],'usage':{'input_tokens':1,'output_tokens':1,'total_tokens':2}}
  events=[('response.created',{'type':'response.created','response':{**response,'status':'in_progress','output':[]}}),('response.output_item.added',{'type':'response.output_item.added','output_index':0,'item':item}),('response.output_item.done',{'type':'response.output_item.done','output_index':0,'item':item}),('response.completed',{'type':'response.completed','response':response})]
  self.send_response(200);self.send_header('content-type','text/event-stream');self.send_header('Connection','close');self.end_headers()
  for name,event in events:self.wfile.write(('event: '+name+'\ndata: '+json.dumps(event)+'\n\n').encode())
  self.wfile.flush()
ThreadingHTTPServer(('127.0.0.1',8899),Handler).serve_forever()
