source "https://rubygems.org"
ruby RUBY_VERSION

# Ruby 3.4+ Windows: eski google-protobuf/sass-embedded sürümleri derlenmiyor
gem 'google-protobuf', '>= 4.35'
gem 'sass-embedded', '>= 1.80'
gem 'csv'
gem 'base64'

# Hello! This is where you manage which Jekyll version is used to run.
# When you want to use a different version, change it below, save the
# file and run `bundle install`. Run Jekyll with `bundle exec`, like so:
#
#     bundle exec jekyll serve
#

# wdm 0.1.1 Ruby 3.4+ ile derlenmiyor; Jekyll file watching için listen kullanır
# gem 'wdm', '>= 0.1.0' if Gem.win_platform?
group :jekyll_plugins do
    gem 'jekyll-feed'
    gem 'jekyll-sitemap'
    gem 'jekyll-paginate'
    gem 'jekyll-seo-tag'
    gem 'jekyll-archives'
    gem 'jekyll-figure'
    gem 'jekyll-gist'
    gem 'kramdown'
    gem 'rouge'
    gem 'webrick'
end