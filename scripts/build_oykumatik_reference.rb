#!/usr/bin/env ruby
# frozen_string_literal: true

require 'open3'
require 'pathname'

ROOT = Pathname.new(__dir__).join('..').expand_path
PY = ROOT.join('scripts', 'build_oykumatik_reference.py')

status = system('python', PY.to_s)
exit($?.exitstatus || 1) unless status

puts 'Öykümatik referans tamamlandı.'
