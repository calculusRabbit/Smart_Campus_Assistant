import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import time
import re
import os

from config import EVENTS_PATH
BASE_URL = "https://www.wichita.edu/calendar/index.php"
OUTPUT_FILE = EVENTS_PATH

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def parse_description(soup):
    desc_el = soup.select_one('[itemprop="description"]')
    if not desc_el:
        return ""
    for br in desc_el.find_all("br"):
        br.replace_with(" ")
    return clean_text(desc_el.get_text())

def should_keep(start_date_str, categories):
    try:
        event_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    except:
        print(f"could not parse date: '{start_date_str}' => keeping it")
        return True

    today = datetime.now()

    if "Academic Calendar" in categories:
        cutoff = today - timedelta(days=180) # i feel like no need calendar like withdraw date in last semester 6 months
    else:
        cutoff = today - timedelta(days=(365)) # dont keep event older than 1 year

    return event_date >= cutoff

def format_chunk(data):
    text = f"{data['title']} on {data['start_date']}"

    if data["end_date"] and data["end_date"] != data["start_date"]:
        text += f" to {data['end_date']}"

    if data["time"]:
        text += f" at {data['time']}"

    if data["location"]:
        text += f" in {data['location']}"

    text += "."

    if data["description"] and data["description"].lower() != data["title"].lower():
        text += " " + data["description"] + "."

    if data["categories"]:
        text += " This event is about " + ", ".join(data["categories"]) + "."

    if data["cost"]:
        text += " It is " + data["cost"] + "."

    return text

def scrape_event(eid):
    url_link = BASE_URL + "?eID=" + str(eid)

    # fetch page 
    try:
        res = requests.get(url_link, timeout=10)
        print("http code: ", res.status_code)
    except requests.RequestException as e:
        print(f"request error: {e}")
        return None

    soup = BeautifulSoup(res.text, "html.parser")


    # check if valid event page 
    article = soup.find("article", class_= "wsu_calendar_event_display")
    if not article:
        print("no article tag found, not a valid event page")
        return None


    # get title
    title = article.find("h1", itemprop="name")
    if title:
        title = clean_text(title.get_text())
    if not title:
        print("article found but no title, skipping")
        return None
    print("TITLE: ", title)


    # get dates
    calendar = article.find("add-to-calendar-button")
    if calendar:
        start_date = calendar.get("startdate", "")
        end_date = calendar.get("enddate", "")
        print(f"START DATE: {start_date} | END DATE: {end_date}")
    else:
        start_date = end_date = ""


    # get time start and end event
    time_element = article.find("time", itemprop="startDate")

    if time_element:
        time_text = clean_text(time_element.get_text())
    else:
        time_text = ""

    print(f"TIME: {time_text}")


    # get cost 
    cost = ""
    event_details = article.find("div", id="event-details")
    if event_details:
        for p in event_details.find_all("p"):
            text = p.get_text()
            if "Cost:" in text:
                cost = clean_text(text.replace("Cost:", "").strip())
                break
    print("COST(MONEY):", cost)


    # get location
    location = ""
    loc_element = article.find("a", itemprop="location")
    if loc_element:
        location = clean_text(loc_element.get_text())
    print("LOCATION: ", location)


    #get categories
    categories = []
    for a in article.find_all("a", itemprop="eventType"):
        categories.append(clean_text(a.get_text()))
    print("CATEGORIES: ", categories)


    # GET DESCRIPTION IMPRTANȚT FOR RAG
    description = parse_description(article)
    print("DESCRIPTION:\n", description)


    # apply date filter, ONLY keep events within last 6 or 7 months 
    if not should_keep(start_date, categories):
        print(f"FILTERED OUT: date {start_date} is too old")
        return None

    data = {
        "source": "event",
        "eid": eid,
        "url": url_link,
        "title": title,
        "start_date": start_date,
        "end_date": end_date,
        "time": time_text,
        "cost": cost,
        "location": location,
        "categories": categories,
        "description": description
    }
    data["chunk_text"] = format_chunk(data)
    return data


def find_existing(chunks, title):
    for c in chunks:
        if c["title"] == title:
            return c
    return None


def main():
    EID_end = 20000
    EID_start = 33000
    delay_time = 0.3
    save_every = 50

    os.makedirs("data", exist_ok=True)


    chunks = []
    total_saved = 0
    for i, eid in enumerate(range(EID_start, EID_end - 1, -1)):
        print("Scraping...")

        event = scrape_event(eid)

        if event:
            existing = find_existing(chunks, event["title"])
            if existing:
                if event["start_date"] < existing["start_date"]:
                    existing["start_date"] = event["start_date"]
                if event["start_date"] > existing["end_date"]:
                    existing["end_date"] = event["start_date"]
                existing["chunk_text"] = format_chunk(existing)
                print(f"MERGED: {event['title']} (range now {existing['start_date']} to {existing['end_date']})")
            else:
                chunks.append(event)
                total_saved += 1
                print(f"SAVED EID {eid}: {event['title']}")
                print("CHUNK TEXT:", event["chunk_text"])
        else:
            print(f"eID {eid} skipped")

        if i > 0 and i % 100 == 0: 
            with open(OUTPUT_FILE, "w",  encoding="utf-8") as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)
            print(f"saved - {total_saved} events so far")

        time.sleep(delay_time)

    with open(OUTPUT_FILE, "w",  encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print("DONE" , {total_saved})


if __name__ == "__main__":
    main()




#references:

"""<!DOCTYPE html>
<html lang="en">
<head>
	<meta http-equiv="Content-Type" content="text/html;charset=UTF-8">
	<title>WSU Event: Entrepreneur-in-Residence Keynote: 'The New Wave of Innovation' - Thursday, May 07, 2026</title>
	<link rel="stylesheet" type="text/css" href="https://www.wichita.edu/calendar/themes/core.css" />
		
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width">
<script>
(function() {
    var origCreateElement = document.createElement;
    document.createElement = function(tagName) {
        var el = origCreateElement.apply(this, arguments);
        if (tagName && typeof tagName === 'string' && tagName.toLowerCase() === 'iframe') {
            el.setAttribute('title', 'Embedded content');
            setTimeout(function() {
                if (el.className && typeof el.className === 'string' && el.className.indexOf('instagram') !== -1) {
                    el.setAttribute('title', 'Instagram embedded post');
                } else if (el.src) {
                    if (el.src.indexOf('youtube') !== -1 || el.src.indexOf('youtu.be') !== -1) el.setAttribute('title', 'YouTube video');
                    else if (el.src.indexOf('vimeo') !== -1) el.setAttribute('title', 'Vimeo video');
                    else if (el.src.indexOf('twitter.com') !== -1 || el.src.indexOf('x.com') !== -1) el.setAttribute('title', 'Twitter embedded post');
                    else if (el.src.indexOf('facebook') !== -1) el.setAttribute('title', 'Facebook embedded content');
                }
            }, 0);
        }
        return el;
    };
})();
</script>

<link rel="stylesheet" href="https://www.wichita.edu/_resources/css/pattern-scaffolding.css" media="all">
<link rel="stylesheet" href="https://www.wichita.edu/_resources/css/style.css?rnd=202603171737" media="all">
<link rel="stylesheet" href="https://www.wichita.edu/_resources/css/oustyles.css"/>
<link rel="stylesheet" href="https://www.wichita.edu/_resources/ldp/galleries/slick/slick.css" />
<link rel="stylesheet" href="https://www.wichita.edu/_resources/ldp/galleries/slick/slick-theme.css" />
<link rel="stylesheet" href="https://www.wichita.edu/_resources/ldp/galleries/slick/slick-caption.css" />
<link rel="stylesheet" href="https://www.wichita.edu/_resources/css/print.css?rnd=202503202005" />
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js" integrity="sha512-v2CJ7UaYy4JwqLDIrZUI/4hqeoQieOmAZNXBeQyjo21dadnwR+8ZaIJVT8EE2iyI61OV8e6M8PP2/4hpQINQ/g==" crossorigin="anonymous" referrerpolicy="no-referrer"></script><!--
lib.min.js combines all of the libraries we are using
except jquery. See the project gulpfile for complete details.
-->
<script src="https://www.wichita.edu/_resources/js/jquery.fitvids.js" defer></script><!--
This modernizr library is custom built by gulp after scanning CSS files.
It will change often during production.
-->
<script src="https://www.wichita.edu/_resources/js/modernizr-custom.js" ></script>
<script src="https://www.wichita.edu/_resources/js/foundation.core.js" defer></script>
<script src="https://www.wichita.edu/_resources/js/foundation.util.box.js" defer></script>
<script src="https://www.wichita.edu/_resources/js/foundation.util.keyboard.js" defer></script>
<script src="https://www.wichita.edu/_resources/js/foundation.util.motion.js" defer></script>
<script src="https://www.wichita.edu/_resources/js/foundation.util.nest.js" defer></script>
<script src="https://www.wichita.edu/_resources/js/foundation.util.timerAndImageLoader.js" defer></script>
<script src="https://www.wichita.edu/_resources/js/foundation.util.touch.js" defer></script>
<script src="https://www.wichita.edu/_resources/js/foundation.util.triggers.js" defer></script>
<script src="https://www.wichita.edu/_resources/js/foundation.util.mediaQuery.js" defer></script>
<script src="https://www.wichita.edu/_resources/js/foundation.accordion.js" defer></script>
<script src="https://www.wichita.edu/_resources/js/foundation.equalizer.js" defer></script>
<script src="https://www.wichita.edu/_resources/js/foundation.tabs.js" defer></script>
<script src="https://www.wichita.edu/_resources/js/foundation.zf.responsiveAccordionTabs.js" defer></script>
<script src="https://cdn.jsdelivr.net/npm/add-to-calendar-button@2" async defer></script>


<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=UA-272026-1"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'UA-272026-1');
</script>
<!-- Google Tag Manager --> 
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start': 
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0], 
j=d.createElement(s),dl=l!='dataLayer'?'&amp;l='+l:'';j.async=true;j.src= 
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f); 
})(window,document,'script','dataLayer','GTM-MHGLJ47');</script> 
<!-- End Google Tag Manager -->
<!-- Google Tag Manager WSU initiated -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-WTTFZLZ');</script>
<!-- End Google Tag Manager 2-->
<!-- Facebook Pixel Code -->
<script>
  !function(f,b,e,v,n,t,s)
  {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
  n.callMethod.apply(n,arguments):n.queue.push(arguments)};
  if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
  n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];
  s.parentNode.insertBefore(t,s)}(window, document,'script',
  'https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', '189100839458926');
  fbq('track', 'PageView');
</script>
<!-- End Facebook Pixel Code --> 

<!-- Hotjar Tracking Code -->
<script>
    (function(h,o,t,j,a,r){
        h.hj=h.hj||function(){(h.hj.q=h.hj.q||[]).push(arguments)};
        h._hjSettings={hjid:3915390,hjsv:6};
        a=o.getElementsByTagName('head')[0];
        r=o.createElement('script');r.async=1;
        r.src=t+h._hjSettings.hjid+j+h._hjSettings.hjsv;
        a.appendChild(r);
    })(window,document,'https://static.hotjar.com/c/hotjar-','.js?sv=');
</script>
<!-- End Hotjar -->

<script src="https://app.heyhalda.com/widgets/smart-forms/cl1uwshzn02y408w1ph1vt3db.js" async defer></script>
	<link rel="stylesheet" type="text/css" href="https://www.wichita.edu/calendar/themes/wichita/css/style.css" />
	<script>
	//<!--
	var listDivs = ["hc_featured","hc_popular","hc_newest"];
	var listLinks = ["hc_l","hc_c","hc_r"];
	function toggleList(b){for(var a=0;a<listDivs.length;)a==b?(document.getElementById(listDivs[a]).style.display="block",document.getElementById(listLinks[a]).setAttribute("aria-selected","true"),document.getElementById(listLinks[a]).className="on"):(document.getElementById(listDivs[a]).style.display="none",document.getElementById(listLinks[a]).setAttribute("aria-selected",
"false"),document.getElementById(listLinks[a]).className="off"),a++};
	
	//-->
	</script>

	<script src="https://www.wichita.edu/calendar/inc/javascript/validation.js"></script>
</head>

<header class="global-header">
   <div class="global-header__utility">
      <nav class="utility-nav" role="navigation" aria-label="Utility Navigation">
         <div class="toplinks__buttons"><a href="/administration/president/ChiefStaff.php" class="button">Leadership</a><a href="/about/innovation/index.php" class="button">Innovation at WSU</a><a href="/research/index.php" class="button">Research</a><a href="/directories/index.php" class="button">Directories</a><a href="https://give.wichita.edu/main-giving-form/?a=11178386" class="button" target="_blank" rel="noopener">Give to WSU</a><a href="https://mywsu.wichita.edu/" class="button">myWSU</a><a href="https://wichita.edu/onestop" class="button">OneStop</a></div>
         <div class="quicklinks"><button class="quicklinks__toggle utility-button">Quick Links<svg class="icon" title="Open Quicklinks"><use xlink:href="/_resources/images/sprites/svg-sprite-custom-symbol.svg#design--menu"></use></svg></button><nav class="quicklinks__overlay" aria-label="Quick Links">
               <div class="quicklinks__overlay-wrapper"><button class="quicklinks__toggle"><svg class="icon" title="Close Menu"><use xlink:href="/_resources/images/sprites/svg-sprite-custom-symbol.svg#design--close"></use></svg><span class="show-for-sr">Close Menu</span></button>
                  <form class="search-bar" action="/search/">
	<div class="search-bar__form">
		<label class="show-for-sr" for="searchField">Search</label> 
		<input name="q" class="" type="text" placeholder="Search This Site" id="searchField"/> <input type="submit" class="button" value="Search"/>
	</div>
</form>
							
<div class="quicklinks__nav-wrapper">
                     <nav class="main-nav" role="navigation" aria-label="Quick Link Main Navigation"><button class="menu-toggle quicklinks__toggle button--accent button--large"><svg class="icon" title="Open Menu"><use xlink:href="/_resources/images/sprites/svg-sprite-custom-symbol.svg#design--menu"></use></svg><span class="show-for-sr">Close Menu</span></button><div class="main-nav__links"><a href="/academics/index.php">ACADEMICS</a><a href="/admissions/index.php">ADMISSIONS</a><a href="/student_life/index.php">STUDENT LIFE</a><a href="https://goshockers.com" target="_blank">ATHLETICS</a><a href="/about/index.php">ABOUT</a><a href="https://my.wsu-info.org/apply-get-started">APPLY NOW</a></div>
                     </nav>
                     <div class="quicklinks__list toplinks__list">
                        <ul>
                           <li><a href="/administration/president/ChiefStaff.php">Leadership</a></li>
                           <li><a href="/about/innovation/index.php">Innovation at WSU</a></li>
                           <li><a href="/research/index.php">Research</a></li>
                           <li><a href="/directories/index.php">Directories</a></li>
                           <li><a href="https://give.wichita.edu/main-giving-form/?a=11178386" target="_blank" rel="noopener">Give to WSU</a></li>
                           <li><a href="https://mywsu.wichita.edu/">myWSU</a></li>
                           <li><a href="https://wichita.edu/onestop">OneStop</a></li>
                        </ul>
                     </div>
                     <div class="quicklinks__list">
                        <ul>
                           <li><a href="/services/registrar/academic_calendar.php" target="_self">Academic Calendar</a></li>
                           <li><a href="https://my.wsu-info.org/apply-get-started" target="_self">Apply Now!</a></li>
                           <li><a href="/directories/directory-a-z.php" target="_self">A-Z Directory</a></li>
                           <li><a href="https://blackboard.wichita.edu/" target="_blank" rel="noopener">Blackboard</a></li>
                           <li><a href="/calendar/" target="_self">Campus Events</a></li>
                           <li><a href="https://jobs.wichita.edu" target="_self">Careers and Employment</a></li>
                           <li><a href="/about/office_hours/index.php" target="_self">Office Hours</a></li>
                           <li><a href="/about/policy/index.php" target="_self">Policies and Procedures</a></li>
                           <li><a href="/services/registrar/schedule_of_courses.php" target="_self">Schedule of Courses</a></li>
                           <li><a href="https://wichita.campuslabs.com/engage/events" target="_self">ShockerSync - Student Events</a></li>
                           <li><a href="https://shockerstore.com" target="_blank" rel="noopener">Shocker Store</a></li>
                           <li><a href="https://portal.office.com" target="_blank" rel="noopener">Student Webmail</a></li>
                           <li><a href="/services/its/userservices/index.php" target="_self">Technology HelpDesk</a></li>
                           <li><a href="/admissions/undergraduate/transfertowsu/index.php" target="_self">Transfer to WSU</a></li>
                           <li><a href="/services/libraries/index.php" target="_blank" rel="noopener">University Libraries</a></li>
                        </ul>
                     </div>
                  </div>
               </div>
            </nav>
         </div><button class="utility-button search-toggle"><svg class="icon" title="Open Search"><use xlink:href="/_resources/images/sprites/svg-sprite-custom-symbol.svg#design--search"></use></svg>Search</button></nav>
   </div>
   <div class="global-header__main">
      <div class="global-header__logo"><a href="/" class="logo"><img src="/_resources/images/logo.svg" alt="Wichita State University Logo"></a><img src="/_resources/images/logo-blacktype.svg" alt="Wichita State University Logo" class="print_logo"></div>
      <nav class="main-nav" role="navigation" aria-label="Main Navigation"><button class="menu-toggle quicklinks__toggle button--accent button--large"><svg class="icon" title="Open Menu"><use xlink:href="/_resources/images/sprites/svg-sprite-custom-symbol.svg#design--menu"></use></svg><span class="show-for-sr">Close Menu</span></button><div class="main-nav__links"><a href="/academics/index.php">ACADEMICS</a><a href="/admissions/index.php">ADMISSIONS</a><a href="/student_life/index.php">STUDENT LIFE</a><a href="https://goshockers.com" target="_blank">ATHLETICS</a><a href="/about/index.php">ABOUT</a><a href="https://my.wsu-info.org/apply-get-started">APPLY NOW</a></div>
      </nav>
   </div>
</header>  
<main class="main">
	 <header class="page-header page-header--hero">
		<div class="page-header__bar">
		   <div class="page-header__page-title">
			  <h1 class="headline-group"><span class="head">Entrepreneur-in-Residence Keynote: 'The New Wave of Innovation'</span></h1>
		   </div>
		   <div class="section-nav">
			  <div class="section-nav__toggle">
				 <div class="section-nav__toggle-wrapper">
				 	<div class="button-collection">
					<a href="/calendar/index.php?com=submit" class="button button--accent button--ondark" roll="button">Submit an Event<svg class="icon button__trailing-icon " title=" "><use xlink:href="/_resources/images/sprites/svg-sprite-custom-symbol.svg#design--arrow-right"></use></svg></a>
				 	<button class="toggleSectionNav primary-toggle">Section Menu <svg class="icon" title="Open Section Links"><use xlink:href="/_resources/images/sprites/svg-sprite-custom-symbol.svg#design--menu"></use></svg></button>
				 	</div>
				 </div>
			  </div>
			  <nav>
	<ul>
		<li><a href="https://www.wichita.edu/calendar/index.php" >Events</a></li>
		<li><a href="https://www.wichita.edu/calendar/index.php?com=submit" >Submit Event</a></li>
		<li><a href="https://www.wichita.edu/calendar/index.php?com=tools" >Tools</a></li>
		<li><a href="https://www.wichita.edu/calendar/index.php?com=digest" >What's New</a></li>

	</ul>
              </nav>
		   </div>
		</div>		<div class="page-header__hero">
			<img src="https://www.wichita.edu/_resources/images/_calendar/woolsey-198_3000x2250.jpg" alt="Photo of Entrepreneur-in-Residence Keynote: 'The New Wave of Innovation'" />
		</div>
		
	 </header>
	</section>

<div class="main-wrapper">
	<section class="main-content" id="main">
	<article itemscope itemtype="http://schema.org/Event" class="wsu_calendar_event_display">
	<header class="collection__header"><h1 itemprop="name" class="heading3">Entrepreneur-in-Residence Keynote: 'The New Wave of Innovation'</h1></header>
	<div class="row" >
	<div class="col-3">
					<add-to-calendar-button
			name="Entrepreneur-in-Residence Keynote: 'The New Wave of Innovation'"
			description="Lauren Dunford will keynote at Wichita State on AI, robotics, manufacturing, and energy shaping the "
			startDate="2026-05-07"
			endDate="2026-05-07"			startTime="09:30:00",
			endTime="10:30:00",
			location=""
			options="['Apple','Google','iCal','Microsoft365','MicrosoftTeams','Outlook.com','Yahoo']"
			timeZone="America/Chicago"
			iCalFileName="Entrepreneur in Residence Keynote The New Wave of Innovation 2026 05 07"
			>
			</add-to-calendar-button>
		<div id="event-details">
			<h3 class="date heading5" style="margin-top: 0;">Thursday, May 7</h3>
			<p><strong>Time: </strong> <time itemprop="startDate" content="2026-05-07T09:30:00-05:00"> 9:30 a.m. - 10:30 a.m.</time></p>
					<div itemscope itemprop="location" itemtype="http://schema.org/Place">
			<h3 class="location heading5">Location:</h3> 
			<p><a href="https://www.wichita.edu/calendar/index.php?com=location&lID=198">Woolsey Hall</a> 
			</p>
					<div itemprop="address" itemscope itemtype="http://schema.org/PostalAddress" style="margin-top: -1em;">
				<span itemprop="streetAddress">1845 Fairmount<br/>
				</span>
				<span itemprop="addressLocality">Wichita</span>, <span itemprop="addressRegion">KS</span>
				<span itemprop="postalCode">67260</span><br/>
				<span itemprop="addressCountry"></span>
			</div>
		<div style="margin-top: 10px;"><a href="https://map.concept3d.com/?id=1128#!ce/27737?m/635250?s/Woolsey%2520Hall?mc/37.718757999999994,-97.288139?z/16?lvl/0" class="link--rich"><span>View on Campus Map<meta itemprop="latitude" content="37.71904028542131" />
<meta itemprop="longitude" content="-97.28814400001261" /></span></a></div>			</div>
					</div>
	<hr>
	<h3 class="heading5">Event Contact</h3>
<p>Jenn Lopez</br><strong>Email</strong>: <a href="mailto:jenn.lopez@wichita.edu">jenn.lopez@wichita.edu</a></br></p>
	</div>
	<div class="col-6">
		<div id="event-description">
		<span itemprop="description"><p>Lauren Dunford will keynote at Wichita State on AI, robotics, manufacturing, and energy shaping the global economy and future innovation.</p>
<p>As part of its Centennial celebration, the Barton School of Business welcomes Lauren Dunford &mdash; CEO and Co-Founder of Guidewheel and a global leader in AI-driven manufacturing &mdash; as Entrepreneur-in-Residence.</p>
<p>Join us for a keynote exploring how artificial intelligence, robotics, and advanced manufacturing are transforming industries and redefining the future of energy.</p>
<p>Dunford is a World Economic Forum Technology Pioneer and TED speaker whose company helps manufacturers worldwide boost productivity while reducing energy costs and emissions. Her work sits at the forefront of "physical AI," bringing intelligence to the machines that power the global economy.</p>
<p>This forward-looking discussion will offer valuable insights for students, faculty, industry professionals, and anyone interested in how innovation is reshaping business and society.<br /><br /><strong>Event Details</strong></p>
<p><strong>Date:</strong>&nbsp;Thursday, May 7, 2026<br /><strong>Time:</strong> 9:30&ndash;10:30 a.m. (Doors open at 9 a.m.)<br /><strong>Location:</strong>&nbsp;Woolsey Auditorium, Wichita State University</p>
<p><strong>Why Attend:</strong></p>
<ul>
<li>Hear from a leading voice in AI, manufacturing, and sustainability</li>
<li>Learn how emerging technologies are reshaping the global economy</li>
<li>Connect with students, faculty, alumni, and industry leaders</li>
<li>Be part of Barton&rsquo;s Centennial Signature Initiative</li>
</ul>
<p><strong>Registration:</strong><br />Reserve your spot today. Seating is limited.</p>
<p><strong>Additional Information:</strong><br />Parking and campus map: <a href="https://map.concept3d.com/?id=1128#!ce/24624?ct/51577?m/889697?s/">https://map.concept3d.com/?id=1128#!ce/24624?ct/51577?m/889697?s/</a>&nbsp;</p></span>
				</div><h3 class="heading5">Share this Event:</h3>
<div class="a2a_kit a2a_kit_size_32 a2a_default_style">
<a class="a2a_dd" href="https://www.addtoany.com/share"></a>
<a class="a2a_button_linkedin"></a>
<a class="a2a_button_facebook"></a>
<a class="a2a_button_twitter"></a>
<a class="a2a_button_reddit"></a>
<a class="a2a_button_email"></a>
</div>
	</div>	<div class="col-3">
		<h3 class="heading5">Categories:</h3>
		<div id="categories">
			<div class="wsu_cal_listing">
	<ul class="wsu_cal_event_list">
<li><a itemprop="eventType" href="https://www.wichita.edu/calendar/index.php?t=53" rel="nofollow">Barton School of Business</a></li>
<li><a itemprop="eventType" href="https://www.wichita.edu/calendar/index.php?t=45" rel="nofollow">Colleges and Schools</a></li>
<li><a itemprop="eventType" href="https://www.wichita.edu/calendar/index.php?t=196" rel="nofollow">Lectures</a></li>

	</ul>
</div>
		</div>
	</div>
</div> <!-- end row -->
</article>
</section>
</div>

<script type="text/javascript" src="//s7.addthis.com/js/300/addthis_widget.js#pubid=ra-5d928d96722e765c"></script>
<section class="teaser-collection section-wrap section-wrap--shade-light collection--four-columns">
	<header class="section-header section-header--no-border collection__header">
		<h2>Other Calendars</h2>
	</header>
	<div class="collection__items">

		<div class="teaser collection__item ">
			<div class="teaser__image"><a href="https://www.wichita.edu/services/registrar/academic_calendar.php"><img src="https://www.wichita.edu/calendar/themes/wichita/img/academic_events.jpg" alt="decorative" /></a></div>
			<div class="teaser__body">
				<div class="teaser__headline">
					<h3 class="headline-group "><a href="https://www.wichita.edu/services/registrar/academic_calendar.php" class="head link--rich"><span>Academic Calendar</span></a></h3>
				</div>
				<div class="teaser__editorial">
					<p>Significant dates and deadlines related to WSU classes.</p>
				</div>
			</div>
		</div>
		<div class="teaser collection__item ">
			<div class="teaser__image"><a href="https://goshockers.com"><img src="https://www.wichita.edu/calendar/themes/wichita/img/athletic_events.jpg" alt="decorative" /></a></div>
			<div class="teaser__body">
				<div class="teaser__headline">
					<h3 class="headline-group "><a href="https://goshockers.com" class="head link--rich"><span>Athletic Events</span></a></h3>
				</div>
				<div class="teaser__editorial">
					<p>Schedule of Wichita State Go Shockers sporting events.</p>
				</div>
			</div>
		</div>
		<div class="teaser collection__item ">
			<div class="teaser__image"><a href="https://wichita.edu/discoverwsu"><img src="https://www.wichita.edu/calendar/themes/wichita/img/community_events.jpg" alt="decorative" /></a></div>
			<div class="teaser__body">
				<div class="teaser__headline">
					<h3 class="headline-group "><a href="https://wichita.edu/discoverwsu" class="head link--rich"><span>Community Events</span></a></h3>
				</div>
				<div class="teaser__editorial">
					<p>Haven’t been to campus lately? Rediscover Wichita State and take advantage of all the events, resources and fun open to the whole community.</p>
				</div>
			</div>
		</div>
		<div class="teaser collection__item ">
			<div class="teaser__image"><a href="https://wichita.campuslabs.com/engage/events"><img src="https://www.wichita.edu/calendar/themes/wichita/img/interfest_800x450.jpg" alt="decorative" /></a></div>
			<div class="teaser__body">
				<div class="teaser__headline">
					<h3 class="headline-group "><a href="https://wichita.campuslabs.com/engage/events" class="head link--rich"><span>ShockerSync Calendar</span></a></h3>
				</div>
				<div class="teaser__editorial">
					<p>Official events from recognized student organizations, fraternities, sororities, and sports clubs.</p>
				</div>
			</div>
		</div>
	</div>
</section>

	</main>

	<footer class="main-footer">
   <section class="footer-top">
      <div class="footer-top--logo-address"><a href="https://www.wichita.edu" class="logo"><img src="/_resources/images/logo-secondary.svg" alt="WSU logo"></a><div class="vcard">
            <div class="adr">
               <div class="street-address">1845 Fairmount St.</div><span class="locality">Wichita</span>,
               							<span class="region">Kansas</span>&nbsp; <span class="postal-code">67260</span><div class="country-name">USA</div>
            </div>
            <div class="tel">(316) 978-3456</div>
         </div>
      </div>
      <div class="footer-top--links">
         <div class="button-collection"><a href="https://www.wichita.edu/about/rfi_splitter_lp.php" role="button" class="button">Request Info</a><a href="/admissions/visit_campus.php" role="button" class="button">Visit</a><a href="https://my.wsu-info.org/apply-get-started" role="button" class="button">Apply</a></div>
         <div class="link-collection"><a href="mailto:operator@wichita.edu?subject=Contact%20Wichita%20State" class=" link--has-icon"><svg class="icon icon-leading"><use xlink:href="/_resources/images/sprites/svg-sprite-custom-symbol.svg#social--z-mashup"></use></svg><span>Contact Us</span></a><a href="https://www.youvisit.com/tour/wichita/wichitastate" class=" link--has-icon"><svg class="icon icon-leading"><use xlink:href="/_resources/images/sprites/svg-sprite-custom-symbol.svg#design--map-pin"></use></svg><span>Virtual Tour</span></a><a href="/about/maps_directions.php" class="link--has-icon"><svg class="icon icon-leading"><use xlink:href="/_resources/images/sprites/svg-sprite-custom-symbol.svg#design--map"></use></svg><span>Interactive Map and Directions</span></a></div>
         <div class="footer-top--social-giving footer-top--giving"><a href="https://foundation.wichita.edu/" class="shock-the-world"><img src="/_resources/images/WSUFAE_Horizontal_White_109U.svg" alt="WSU Foundation and Alumni Engagement logo"></a><a href="https://shockerstore.com/store1/home" class="shocker-store"><img src="/_resources/images/sprites/shocker-store.svg" alt="Shocker Store Logo"></a><a href="/about/designations/age-friendly-university.php" class="shocker-store"><img src="/_resources/images/sprites/afu_logo-trimmed.svg" alt="Age Friendly University logo"></a></div>
         <div class="footer-top--social-giving footer-top--social">
            <div class="social-media"><a href="https://www.facebook.com/wichita.state/" class="social__link"><svg class="icon" title="Facebook"><use xlink:href="/_resources/images/sprites/svg-sprite-custom-symbol.svg#social--facebook"></use></svg><span class="show-for-sr">Facebook</span></a><a href="https://twitter.com/wichitastate/" class="social__link"><svg class="icon" title="X | Twitter"><use xlink:href="/_resources/images/sprites/svg-sprite-custom-symbol.svg#social--twitterx"></use></svg><span class="show-for-sr">X | Twitter</span></a><a href="https://www.instagram.com/wichitastateu/" class="social__link"><svg class="icon" title="Instagram"><use xlink:href="/_resources/images/sprites/svg-sprite-custom-symbol.svg#social--instagram"></use></svg><span class="show-for-sr">Instagram</span></a><a href="https://www.youtube.com/channel/UCzLkoHQTEMpWnCnG2Vvphuw/videos" class="social__link"><svg class="icon" title="YouTube"><use xlink:href="/_resources/images/sprites/svg-sprite-custom-symbol.svg#social--youtube"></use></svg><span class="show-for-sr">YouTube</span></a><a href="https://www.linkedin.com/school/wichita-state-university" class="social__link"><svg class="icon" title="Linkedin"><use xlink:href="/_resources/images/sprites/svg-sprite-custom-symbol.svg#social--linkedin"></use></svg><span class="show-for-sr">Linkedin</span></a></div>
         </div>
      </div>
      <div class="footer-top--quote">
         <div class="pullquote">
            <div class="pullquote__quote"><span>(WSU) is unique in how many excellent opportunities students have to get relevant
                  experience on their resume while in college.</span></div><cite class="pullquote__attribution"><span class="pullquote__first-line">Sarah Varner , </span><span class="pullquote__second-line">aerospace engineering major</span></cite></div>
         <div class="link-collection"><a href="https://foundation.wichita.edu/alumni/">Alumni &amp; Friends</a><a href="https://give.wichita.edu/main-giving-form/?a=11178386/">Give to WSU</a></div>
      </div>
   </section>
   <section class="footer-bottom">
      <div class="legal-bucket">
         <div class="link-collection">
            <ul>
               <li><a href="/directories/directory-a-z.php">A-Z&nbsp;Index</a></li>
               <li><a href="https://jobs.wichita.edu">Careers and Employment</a></li>
               <li><a href="/about/free_expression/index.php">Freedom&nbsp;of&nbsp;Expression</a></li>
               <li><a href="/about/policy/index.php">Policies&nbsp;and&nbsp;Procedures</a></li>
               <li><a href="/about/privacy.php">Privacy&nbsp;Policy</a></li>
               <li><a href="/about/policy/ch_03/ch3_02.php">Notice&nbsp;of&nbsp;Nondiscrimination</a></li>
               <li><a href="/administration/oiec/titleixstatement.php">Title&nbsp;IX</a></li>
               <li><a href="/services/emergency/index.php">Campus&nbsp;Safety</a></li>
               <li><a href="/services/mrc/access/index.php">Accessibility</a></li>
               <li><a href="/about/public_information/index.php">Public&nbsp;Information</a></li>
               <li><a href="https://learn.wichita.edu/">Website&nbsp;Support</a></li>
               <li><a href="/about/free_expression/kbor_foe_statement.php">KBOR Freedom of Expression Statement</a></li>
               <li><a href="/academics/academic_affairs/hlc/index.php">HLC Accreditation</a></li>
            </ul>
         </div>
         <p><span class="copyright"><span id="directedit">© </span>2026 Wichita State University</span></p>
      </div>
      <div class="degree-stats"><a href="https://ksdegreestats.org/" class=""><img src="/_resources/images/degree-stats-logo.svg" alt="footer-lbbgogo"></a></div>
   </section>
   <section class="footer-top footer-titleix">Wichita State University (“WSU”) does not discriminate on the basis of sex in its
      education programs, activities, admissions and employment.</section>
</footer>	
<script src="https://www.wichita.edu/_resources/js/svg4everybody.js" defer></script> 
<script src="https://www.wichita.edu/_resources/js/main.js?v=202511111803" defer></script> 
<script src="https://www.wichita.edu/_resources/js/direct-edit.js?v=20220920910" defer></script>
<script src="https://www.wichita.edu/_resources/js/nav_inc.js" defer></script>
<script src="https://www.wichita.edu/_resources/ldp/galleries/slick/slick.min.js" defer></script>
<script src="https://www.wichita.edu/_resources/ldp/galleries/slick/slick-start.js" defer></script>
<script src="https://www.wichita.edu/_resources/js/mc-forms-theme.js" defer async></script>
<script>
$(function () {
    var $accordionTarget = $(window.location.hash);
    if ($accordionTarget.length) {
		$accordionTarget.parents('.accordion-item').addClass('is-active');
    }
});
</script>
<script async src="https://static.addtoany.com/menu/page.js"></script>
<script>
(function(w,d,t,u,n,a,m){w['MauticTrackingObject']=n;
w[n]=w[n]||function(){(w[n].q=w[n].q||[]).push(arguments)},a=d.createElement(t),
m=d.getElementsByTagName(t)[0];a.async=1;a.src=u;m.parentNode.insertBefore(a,m)
})(window,document,'script','https://my.wsu-info.org/mtc.js','mt');
mt('send', 'pageview');
</script>
<!-- End EAB Code -->
		<script src="https://www.wichita.edu/calendar/themes/wichita/js/wichita.js"></script>
</strong>
</html>"""