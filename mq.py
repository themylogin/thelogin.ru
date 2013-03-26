#!/usr/bin/python
# -*- coding: utf-8 -*-

import pika

mq_connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
mq_channel = mq_connection.channel()
