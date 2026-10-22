/* Node includes this runner and assertions: no npm install, Jest or browser.
   Arrange a session, act with explicit timestamps, assert observable results. */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { DURATION_MS, PASSAGES, analyzeText, calculateStats, Session } = require('../sprint.js');

test('original passages are frozen, distinct, single-line ASCII practice text', () => {
  assert.equal(DURATION_MS, 60_000);
  assert.equal(PASSAGES.length, 3);
  assert.ok(Object.isFrozen(PASSAGES));
  assert.equal(new Set(PASSAGES.map(p => p.id)).size, 3);
  for (const passage of PASSAGES) {
    assert.ok(Object.isFrozen(passage));
    assert.ok(passage.title.length > 0);
    assert.ok(passage.text.length >= 250 && passage.text.length <= 400);
    assert.match(passage.text, /^[\x20-\x7e]+$/);
  }
});
for (const [name,target,input,correct,incorrect] of [
  ['empty','abc','',0,0], ['exact','abc','abc',3,0],
  ['partial','abc','ab',2,0], ['wrong','abc','axc',2,1],
  ['spaces','a b','a b',3,0], ['case','Ab','ab',1,1],
  ['punctuation','hi!','hi?',2,1], ['extra','abc','abcd',3,1],
  ['insertions shift positions','abcd','axbcd',1,4],
  ['UTF16 units','😀','😀',2,0]
]) {
  test(`positional analysis: ${name}`, () => {
    const result = analyzeText(target,input);
    assert.equal(result.correct,correct);
    assert.equal(result.incorrect,incorrect);
    assert.equal(result.typed,input.length);
    assert.equal(result.accuracy,input.length ? correct/input.length*100 : 100);
    assert.equal(result.complete,input===target);
  });
}
for (const target of ['',null,42,[],{}]) {
  test(`invalid target ${JSON.stringify(target)}`, () => {
    assert.throws(() => analyzeText(target,''),TypeError);
    assert.throws(() => new Session(target),TypeError);
  });
}
for (const value of [null,42,[],{}]) {
  test(`invalid input ${JSON.stringify(value)}`, () => {
    assert.throws(() => analyzeText('abc',value),TypeError);
    assert.throws(() => new Session('abc').update(value,0),TypeError);
  });
}
for (const value of [-1,NaN,Infinity,-Infinity,'1',null]) {
  test(`invalid elapsed time ${String(value)}`, () => {
    assert.throws(() => calculateStats('abc','a',value),RangeError);
    assert.throws(() => new Session('abc').tick(value),RangeError);
    assert.throws(() => new Session('abc').snapshot(value),RangeError);
  });
}
for (const value of [0,-1,NaN,Infinity,'1',null]) {
  test(`invalid duration ${String(value)}`, () => assert.throws(() => new Session('abc',value),RangeError));
}
test('WPM uses matching characters/5/minutes and includes spaces', () => {
  assert.equal(calculateStats('a b c d e f','a b c d e f',30_000).wpm,4.4);
  assert.equal(calculateStats('abcde','abxde',60_000).wpm,0.8);
  assert.equal(calculateStats('abc','abc',0).wpm,0);
  assert.equal(calculateStats('abc','abc',90_000).remainingMs,0);
});
test('ready does not start on focus, tick or empty input', () => {
  const session = new Session('abc');
  session.tick(10_000);
  const result = session.update('',20_000);
  assert.equal(result.state,'ready');
  assert.equal(result.elapsedMs,0);
  assert.equal(result.remainingMs,60_000);
  assert.equal(session.startedAt,null);
});
test('first nonempty input starts clock including timestamp zero', () => {
  const session = new Session('abc');
  session.update('a',0);
  const result = session.tick(1000);
  assert.equal(session.startedAt,0);
  assert.equal(result.state,'running');
  assert.equal(result.elapsedMs,1000);
  assert.equal(result.remainingMs,59_000);
});
test('Backspace corrects current accuracy but does not restart timer', () => {
  const session = new Session('abcd');
  session.update('ax',100);
  assert.equal(session.snapshot(100).accuracy,50);
  session.update('a',200);
  assert.equal(session.snapshot(200).accuracy,100);
  session.update('',300);
  assert.equal(session.state,'running');
  assert.equal(session.startedAt,100);
  assert.equal(session.snapshot(300).elapsedMs,200);
});
test('wrong full length is editable; exact corrected match finishes', () => {
  const session = new Session('abc');
  session.update('abx',0);
  assert.equal(session.state,'running');
  const result = session.update('abc',1000);
  assert.equal(result.state,'finished');
  assert.equal(result.reason,'completed');
  assert.equal(result.elapsedMs,1000);
  assert.equal(result.wpm,36);
});
test('single-event completion has zero elapsed and finite zero speed', () => {
  const result = new Session('abc').update('abc',500);
  assert.equal(result.reason,'completed');
  assert.equal(result.elapsedMs,0);
  assert.equal(result.wpm,0);
});
test('deadline rejects late input and freezes at exact duration', () => {
  const session = new Session('abc');
  session.update('a',100);
  const result = session.update('abc',60_100);
  assert.equal(result.reason,'timeout');
  assert.equal(result.input,'a');
  assert.equal(result.elapsedMs,60_000);
  assert.equal(session.finishedAt,60_100);
});
test('a very late tick must not inflate denominator or duration', () => {
  const session = new Session('abc');
  session.update('ab',100);
  const result = session.tick(300_000);
  assert.equal(result.elapsedMs,60_000);
  assert.equal(result.wpm,0.4);
  assert.equal(result.remainingMs,0);
});
test('input just before deadline can finish normally', () => {
  const session = new Session('abc',1000);
  session.update('a',100);
  const result = session.update('abc',1099);
  assert.equal(result.reason,'completed');
  assert.equal(result.elapsedMs,999);
});
test('custom duration drives remaining time instead of default constant', () => {
  const session = new Session('abc',1500);
  assert.equal(session.snapshot(0).remainingMs,1500);
  session.update('a',100);
  assert.equal(session.tick(600).remainingMs,1000);
  assert.equal(session.tick(2000).elapsedMs,1500);
});
test('finished inputs and result metrics do not change on later calls', () => {
  const session = new Session('abc');
  session.update('a',0);
  const result = session.update('abc',1000);
  assert.deepEqual(session.update('different',2000),result);
  assert.deepEqual(session.tick(100_000),result);
});
test('snapshots do not resolve expiry; tick does', () => {
  const session = new Session('abc',1000);
  session.update('a',0);
  assert.equal(session.snapshot(2000).state,'running');
  assert.equal(session.state,'running');
  assert.equal(session.tick(2000).state,'finished');
});
test('reject backwards times, allow equal timestamps', () => {
  const session = new Session('abc');
  session.tick(10);
  session.update('a',10);
  assert.throws(() => session.tick(9),RangeError);
  assert.throws(() => session.update('b',9),RangeError);
  assert.throws(() => session.snapshot(9),RangeError);
});
test('reset clears input, timestamps, finish state and clock history', () => {
  const session = new Session('abc');
  session.update('abc',1000);
  session.reset();
  assert.equal(session.state,'ready');
  assert.equal(session.input,'');
  assert.equal(session.reason,null);
  assert.equal(session.startedAt,null);
  assert.equal(session.finishedAt,null);
  assert.equal(session.lastNow,null);
  assert.equal(session.tick(0).remainingMs,60_000);
});
