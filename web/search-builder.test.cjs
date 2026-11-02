const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'search-builder.html'),'utf8');
const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
const context={URLSearchParams};
vm.runInNewContext(scripts[0],context);
const b=context.SearchBuilder;
const valid={id:'test',title:'Test',enabled:true,version:'4',lookback_days:14,description:'Förslag',query:'MRI[Title]'};

test('OR within groups and AND between subject and method',()=>{
 const query=b.query({mode:'terms',topic:'knee\nshoulder\nknee',topicField:'Title/Abstract',method:'MRI\ncomputed tomography',methodField:'Title',exclude:'mice'});
 assert.equal(query,'("knee"[Title/Abstract] OR "shoulder"[Title/Abstract]) AND ("MRI"[Title] OR "computed tomography"[Title]) NOT ("mice"[Title/Abstract])');
});
test('optional methods and exclusions introduce no empty operators',()=>{
 assert.equal(b.query({mode:'terms',topic:'knee',topicField:'Title',method:'',methodField:'Title',exclude:''}),'("knee"[Title])');
});
test('advanced syntax must use expert mode rather than inject fields',()=>{
 assert.throws(()=>b.group('knee[All Fields]','Title'));
 assert.throws(()=>b.group('knee" OR anything','Title'));
 assert.throws(()=>b.group('knee','invalid'));
 assert.equal(b.query({mode:'expert',query:' (MRI[Title] OR CT[Title]) '}),'(MRI[Title] OR CT[Title])');
});
test('IDs, nonempty queries, date windows and duplicate IDs are validated',()=>{
 assert.throws(()=>b.yaml([{...valid,id:'../bad'}]));
 assert.throws(()=>b.yaml([valid,valid]));
 assert.throws(()=>b.yaml([{...valid,lookback_days:0}]));
 assert.throws(()=>b.yaml([{...valid,query:''}]));
 assert.doesNotThrow(()=>b.yaml([valid]));
});
test('YAML quotes Unicode and structural-looking user input',()=>{
 const text=b.yaml([{...valid,title:'Knä: "test"',description:'line 1\nline 2'}]);
 assert.ok(text.includes('title: "Knä: \\"test\\""'.replaceAll('\\\\','\\')));
 assert.ok(text.includes('description: "line 1\\nline 2"'));
});
test('PubMed link includes exact UTC EDAT date interval and encoded query',()=>{
 const url=new URL(b.url('knee & MRI',14,new Date('2026-11-02T23:50:00Z')));
 assert.equal(url.hostname,'pubmed.ncbi.nlm.nih.gov');
 assert.equal(url.searchParams.get('term'),'(knee & MRI) AND ("2026/10/20"[EDAT] : "2026/11/02"[EDAT])');
});
test('query changes advance existing versions, new searches start at one',()=>{
 assert.equal(b.version({query:'old',version:'3'},'old'),'3');
 assert.equal(b.version({query:'old',version:'3'},'new'),'4');
 assert.equal(b.version({query:'old',version:'1',isNew:true},'new'),'1');
});
