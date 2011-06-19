#!/usr/bin/env python

import unittest
import fakeredis
import redis


class TestFakeRedis(unittest.TestCase):
    def setUp(self):
        self.redis = self.create_redis()

    def tearDown(self):
        self.redis.flushdb()

    def create_redis(self):
        return fakeredis.FakeRedis()

    def test_set_then_get(self):
        self.redis.set('foo', 'bar')
        self.assertEqual(self.redis.get('foo'), 'bar')

    def test_get_does_not_exist(self):
        self.assertEqual(self.redis.get('foo'), None)

    ## Tests for the list type.

    def test_lpush_then_lrange_all(self):
        self.redis.lpush('foo', 'bar')
        self.redis.lpush('foo', 'baz')
        self.assertEqual(self.redis.lrange('foo', 0, -1), ['baz', 'bar'])

    def test_lpush_then_lrange_portion(self):
        self.redis.lpush('foo', 'one')
        self.redis.lpush('foo', 'two')
        self.redis.lpush('foo', 'three')
        self.redis.lpush('foo', 'four')
        self.assertEqual(self.redis.lrange('foo', 0, 2),
                         ['four', 'three', 'two'])
        self.assertEqual(self.redis.lrange('foo', 0, 3),
                         ['four', 'three', 'two', 'one'])

    def test_lpush_key_does_not_exist(self):
        self.assertEqual(self.redis.lrange('foo', 0, -1), [])

    def test_llen(self):
        self.redis.lpush('foo', 'one')
        self.redis.lpush('foo', 'two')
        self.redis.lpush('foo', 'three')
        self.assertEqual(self.redis.llen('foo'), 3)

    def test_llen_no_exist(self):
        self.assertEqual(self.redis.llen('foo'), 0)

    def test_lrem_postitive_count(self):
        self.redis.lpush('foo', 'same')
        self.redis.lpush('foo', 'same')
        self.redis.lpush('foo', 'different')
        self.redis.lrem('foo', 'same', 2)
        self.assertEqual(self.redis.lrange('foo', 0, -1), ['different'])

    def test_lrem_negative_count(self):
        self.redis.lpush('foo', 'removeme')
        self.redis.lpush('foo', 'three')
        self.redis.lpush('foo', 'two')
        self.redis.lpush('foo', 'one')
        self.redis.lpush('foo', 'removeme')
        self.redis.lrem('foo', 'removeme', -1)
        # Should remove it from the end of the list,
        # leaving the 'removeme' from the front of the list alone.
        self.assertEqual(self.redis.lrange('foo', 0, -1),
                         ['removeme', 'one', 'two', 'three'])

    def test_lrem_zero_count(self):
        self.redis.lpush('foo', 'one')
        self.redis.lpush('foo', 'one')
        self.redis.lpush('foo', 'one')
        self.redis.lrem('foo', 'one', 0)
        self.assertEqual(self.redis.lrange('foo', 0, -1), [])

    def test_lrem_default_value(self):
        self.redis.lpush('foo', 'one')
        self.redis.lpush('foo', 'one')
        self.redis.lpush('foo', 'one')
        self.redis.lrem('foo', 'one')
        self.assertEqual(self.redis.lrange('foo', 0, -1), [])

    def test_lrem_does_not_exist(self):
        self.redis.lpush('foo', 'one')
        self.redis.lrem('foo', 'one')
        # These should be noops.
        self.redis.lrem('foo', 'one', -2)
        self.redis.lrem('foo', 'one', 2)

    def test_lrem_return_value(self):
        self.redis.lpush('foo', 'one')
        count = self.redis.lrem('foo', 'one')
        self.assertEqual(count, 1)
        self.assertEqual(self.redis.lrem('foo', 'one'), 0)

    def test_rpush(self):
        self.redis.rpush('foo', 'one')
        self.redis.rpush('foo', 'two')
        self.redis.rpush('foo', 'three')
        self.assertEqual(self.redis.lrange('foo', 0, -1),
                         ['one', 'two', 'three'])

    def test_lpop(self):
        self.redis.rpush('foo', 'one')
        self.redis.rpush('foo', 'two')
        self.redis.rpush('foo', 'three')
        self.assertEqual(self.redis.lpop('foo'), 'one')
        self.assertEqual(self.redis.lpop('foo'), 'two')
        self.assertEqual(self.redis.lpop('foo'), 'three')

    def test_lpop_empty_list(self):
        self.redis.rpush('foo', 'one')
        self.redis.lpop('foo')
        self.assertEqual(self.redis.lpop('foo'), None)
        # Verify what happens if we try to pop from a key
        # we've never seen before.
        self.assertEqual(self.redis.lpop('noexists'), None)

    def test_lset(self):
        self.redis.rpush('foo', 'one')
        self.redis.rpush('foo', 'two')
        self.redis.rpush('foo', 'three')
        self.redis.lset('foo', 0, 'four')
        self.redis.lset('foo', -2, 'five')
        self.assertEqual(self.redis.lrange('foo', 0, -1),
                         ['four', 'five', 'three'])

    def test_lset_index_out_of_range(self):
        self.redis.rpush('foo', 'one')
        with self.assertRaises(redis.ResponseError):
            self.redis.lset('foo', 3, 'three')

    def test_rpushx(self):
        self.redis.rpush('foo', 'one')
        self.redis.rpushx('foo', 'two')
        self.redis.rpushx('bar', 'three')
        self.assertEqual(self.redis.lrange('foo', 0, -1), ['one', 'two'])
        self.assertEqual(self.redis.lrange('bar', 0, -1), [])

    def test_lindex(self):
        self.redis.rpush('foo', 'one')
        self.redis.rpush('foo', 'two')
        self.assertEqual(self.redis.lindex('foo', 0), 'one')
        self.assertEqual(self.redis.lindex('foo', 4), None)
        self.assertEqual(self.redis.lindex('bar', 4), None)

    def test_lpushx(self):
        self.redis.lpush('foo', 'two')
        self.redis.lpushx('foo', 'one')
        self.redis.lpushx('bar', 'one')
        self.assertEqual(self.redis.lrange('foo', 0, -1), ['one', 'two'])
        self.assertEqual(self.redis.lrange('bar', 0, -1), [])

    def test_rpop(self):
        self.redis.rpush('foo', 'one')
        self.redis.rpush('foo', 'two')
        self.assertEqual(self.redis.rpop('foo'), 'two')
        self.assertEqual(self.redis.rpop('foo'), 'one')
        self.assertEqual(self.redis.rpop('foo'), None)

    def test_linsert(self):
        self.redis.rpush('foo', 'hello')
        self.redis.rpush('foo', 'world')
        self.redis.linsert('foo', 'before', 'world', 'there')
        self.assertEqual(self.redis.lrange('foo', 0, -1),
                         ['hello', 'there', 'world'])

    def test_rpoplpush(self):
        self.redis.rpush('foo', 'one')
        self.redis.rpush('foo', 'two')
        self.redis.rpush('bar', 'one')

        self.redis.rpoplpush('foo', 'bar')
        self.assertEqual(self.redis.lrange('foo', 0, -1), ['one'])
        self.assertEqual(self.redis.lrange('bar', 0, -1), ['two', 'one'])

    def test_blpop_single_list(self):
        self.redis.rpush('foo', 'one')
        self.redis.rpush('foo', 'two')
        self.redis.rpush('foo', 'three')
        self.assertEqual(self.redis.blpop(['foo'], timeout=1), ('foo', 'one'))

    def test_blpop_test_multiple_lists(self):
        self.redis.rpush('foo', 'one')
        self.redis.rpush('foo', 'two')
        # bar has nothing, so the returned value should come
        # from foo.
        self.assertEqual(self.redis.blpop(['bar', 'foo'], timeout=1),
                         ('foo', 'one'))
        self.redis.rpush('bar', 'three')
        # bar now has something, so the returned value should come
        # from bar.
        self.assertEqual(self.redis.blpop(['bar', 'foo'], timeout=1),
                         ('bar', 'three'))
        self.assertEqual(self.redis.blpop(['bar', 'foo'], timeout=1),
                         ('foo', 'two'))

    def test_blpop_allow_single_key(self):
        # blpop converts single key arguments to a one element list.
        self.redis.rpush('foo', 'one')
        self.assertEqual(self.redis.blpop('foo', timeout=1), ('foo', 'one'))

    def test_brpop_test_multiple_lists(self):
        self.redis.rpush('foo', 'one')
        self.redis.rpush('foo', 'two')
        self.assertEqual(self.redis.brpop(['bar', 'foo'], timeout=1),
                         ('foo', 'two'))

    def test_brpop_single_key(self):
        self.redis.rpush('foo', 'one')
        self.redis.rpush('foo', 'two')
        self.assertEqual(self.redis.brpop('foo', timeout=1),
                         ('foo', 'two'))


    def test_brpoplpush_multi_keys(self):
        self.redis.rpush('foo', 'one')
        self.redis.rpush('foo', 'two')
        self.assertEqual(self.redis.brpoplpush('foo', 'bar', timeout=1),
                         'two')
        self.assertEqual(self.redis.lrange('bar', 0, -1), ['two'])


class TestRealRedis(TestFakeRedis):
    integration = True

    def create_redis(self):
        # Using db=10 in the hopes that it's not commonly used.
        return redis.Redis('localhost', port=6379, db=10)


if __name__ == '__main__':
    unittest.main()