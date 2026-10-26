/* Node's built-in test runner: no npm dependencies are needed. */
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { ALGORITHMS, createStepper, createData } = require('../algorithms.js');

/** Tiny deterministic RNG lets us replay a failing random test exactly. */
function random(seed) {
  return () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 2 ** 32; };
}
/** Consume the lazy iterator only in tests; the app never stores full history. */
function events(id, values) { return [...createStepper(id, values)]; }

for (const id of Object.keys(ALGORITHMS)) {
  test(`${id}: metadata describes the actual variant`, () => {
    const meta = ALGORITHMS[id];
    for (const key of ['name','description','best','average','worst','space','explanation']) assert.ok(meta[key].length);
    assert.equal(typeof meta.stable, 'boolean'); assert.ok(meta.steps.length > 0);
  });
  for (const [name, values] of Object.entries({empty:[],single:[1],pair:[2,1],duplicates:[4,2,4,1,2,1],sorted:[1,2,3,4],reversed:[5,4,3,2,1],largeKeys:[999,1,10,100,999,20]})) {
    test(`${id}: ${name} sorts with valid nonmutating snapshots`, () => {
      const copy = values.slice(), wanted = values.slice().sort((a,b) => a-b);
      const history = events(id, values);
      assert.deepEqual(values, copy);
      const final = history.at(-1);
      assert.deepEqual(final.values,wanted); assert.equal(final.done,true);
      assert.deepEqual(final.active,[]);
      assert.deepEqual(final.sorted.slice().sort((a,b)=>a-b),wanted.map((_,i)=>i));
      let previous = {comparisons:0,writes:0,swaps:0,auxWrites:0};
      for (const event of history) {
        assert.equal(event.values.length,values.length);
        assert.equal(typeof event.note,'string'); assert.equal(typeof event.done,'boolean');
        assert.ok(Number.isInteger(event.line) && event.line >= 0 && event.line < ALGORITHMS[id].steps.length);
        for (const field of ['comparisons','writes','swaps','auxWrites']) {
          assert.ok(Number.isSafeInteger(event[field]) && event[field] >= previous[field]);
        }
        for (const index of [...event.active,...event.sorted]) assert.ok(Number.isInteger(index) && index>=0 && index<values.length);
        for (const index of event.sorted) assert.equal(event.values[index],wanted[index]);
        previous=event;
      }
      if (history.length>1) {
        history[0].values[0]=777;
        assert.deepEqual(final.values,wanted); // Earlier event arrays are independent.
      }
    });
  }
  test(`${id}: 25 seeded random inputs and maximum size`, () => {
    for (let seed=0;seed<26;seed++) {
      const rng=random(seed);
      const data=Array.from({length:seed===25?128:8+seed},()=>1+Math.floor(rng()*999));
      let last;
      for (const event of createStepper(id,data)) last=event;
      assert.deepEqual(last.values,data.slice().sort((a,b)=>a-b));
    }
  });
}

test('bubble counts exact comparisons, swaps and main writes', () => {
  const last=events('bubble',[3,2,1]).at(-1);
  assert.equal(last.comparisons,3);assert.equal(last.swaps,3);assert.equal(last.writes,6);assert.equal(last.auxWrites,0);
});
test('sorted bubble exits after one pass', () => assert.equal(events('bubble',[1,2,3,4]).at(-1).comparisons,3));
test('selection avoids meaningless self-swaps', () => assert.equal(events('selection',[1,2,3]).at(-1).swaps,0));
test('counting/radix expose bucket work and main-array writes', () => {
  for (const id of ['counting','radix']) {
    const history=events(id,[30,10,20]);const last=history.at(-1);
    assert.equal(last.comparisons,0);assert.equal(last.swaps,0);
    assert.ok(last.auxWrites>last.writes);assert.ok(history.length>10);
    assert.ok(history.some(e=>e.note.includes('Prefix sums')));
    assert.equal(last.writes,id==='counting'?3:6);
  }
});
test('invalid algorithm/input raises before iteration', () => {
  for (const id of ['unknown','toString','__proto__']) assert.throws(()=>createStepper(id,[1]),RangeError);
  for (const value of [null,{},'123',new Array(3),[0],[-1],[1000],[1.2],[NaN],[Infinity],[true],new Array(129).fill(1)]) assert.throws(()=>createStepper('bubble',value),RangeError);
});
test('iterator captures input at creation, not at first next', () => {
  const source=[3,1,2],iterator=createStepper('merge',source);source[0]=999;
  assert.deepEqual([...iterator].at(-1).values,[1,2,3]);
});
for (const pattern of ['random','sorted','reversed','nearly','few-unique']) {
  test(`createData: ${pattern} bounded and reproducible`, () => {
    for (const size of [8,48,128]) {
      const data=createData(size,pattern,random(123));assert.equal(data.length,size);
      assert.ok(data.every(n=>Number.isInteger(n)&&n>=1&&n<=100));
      assert.deepEqual(data,createData(size,pattern,random(123)));
      if (pattern==='sorted') assert.deepEqual(data,data.slice().sort((a,b)=>a-b));
      if (pattern==='reversed') assert.deepEqual(data,data.slice().sort((a,b)=>b-a));
      if (pattern==='few-unique') assert.ok(new Set(data).size<=5);
    }
  });
}
test('data generation rejects invalid options/RNG', () => {
  for (const n of [0,7,129,9.5,'8']) assert.throws(()=>createData(n,'random'),RangeError);
  assert.throws(()=>createData(8,'unknown'),RangeError);
  for (const v of [-1,1,NaN,Infinity]) assert.throws(()=>createData(8,'random',()=>v),RangeError);
});
