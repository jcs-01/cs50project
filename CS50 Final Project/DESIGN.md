The original idea for my project was to create a hub for all the different Harvard websites that students regularly access. I was hoping to use iframes to collect these websites on the homepage and make it customizable for different users. However, in the process of working on this, I realized that Harvard website security doesn't allow its pages to be embedded into iFrames, so I needed to go a different way.

My new idea combined iframes where possible with web-scraping. The home page includes an iframe from The Crimson and a weather site for Cambridge, both of which can be embedded. It also features Harvard's Twitter feed. I used web scraping to get the HUDS menu and put that on the home page as well. First, I tried doing this using the CS50 API, but then realized that the HUDS website links have changed since then and that no longer works, so I had to change my strategy and make my own request to the page. 

I spent a lot of time on the web scraping, getting rid of extra words around the food items on the page and fixing the link formatting so it works for every house and meal. Now, through the "Choose a Dining Hall" page, it's possible to choose what house and meal you would like to display (as the default for your session when you are logged in) on the home page. 

Another feature of the site is the database of Harvard websites. On the "Harvard Websites" page, a list is displayed of a database I created of commonly used Harvard websites. This database is searchable on the "Search" page. If you want to add a website to this page that isn't there currently, this can be done on the "Add a Website" page. 

In terms of specific code design, I used some base code from finance (including the CSS, register/login/logout, base flask code, and the base of layout.html). From there, I used
-session variables
-web scraping--beautiful soup, requests
-regex


Together, I tried to make all these features add up to something like my original idea. However, I have a lot more ideas I'd like to implement for this project in the future (and would have added if I had more time), including improving the menu's formatting, letting the user look at more dates, letting the user favorite links from the database to show up on the home page, improving the search function, improving the appearance, and more. I enjoyed implementing new features with this project and figuring out how to adapt when I had to change my plans.