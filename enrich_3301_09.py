#!/usr/bin/env python3
"""Enrich remaining 3301/09 files with summary, player_impact, and clean entities."""

import re
import yaml
from pathlib import Path

DIR = Path("Archive/3301/09")

# Data for each file: new frontmatter fields
ENRICHMENTS = {
    "09_imperial_veteran_sceptical_about_patreuss_campaign.md": {
        "persons": ["Denton Patreus", "Anthony Corvus"],
        "groups": ["Imperial Herald", "Imperial Navy"],
        "locations": [],
        "technologies": [],
        "summary": "General Anthony Corvus of the Imperial Navy publicly questioned Senator Denton Patreus's optimism about quickly eradicating Emperor's Dawn. Corvus described the insurgents as a well-organized cell organization that is surprisingly hard to extinguish, with new cells appearing as soon as one is destroyed. Patreus declined to comment on the general's remarks.",
        "player_impact": "None",
        "modern_impact": "GalNet community report documenting current events in the galaxy.",
    },
    "10_new_combat_fighter_from_gutamaya_shipyards.md": {
        "persons": [],
        "groups": ["Gutamaya Shipyards", "Imperial Navy"],
        "locations": [],
        "technologies": ["Imperial Eagle", "Eagle Mk II"],
        "summary": "Gutamaya Shipyards unveiled the Imperial Eagle, a successor to the Eagle Mk II. While slightly less maneuverable, it outclasses its predecessor in speed (300 top, 400 boost), armor, shields, and firepower, replacing the small hardpoint with a medium. Manufactured for the Imperial Navy, it requires Outsider rank or above and retails at 110,825 CR.",
        "player_impact": "Imperial Navy pilots of Outsider rank or higher can purchase the Imperial Eagle, a sleeker and more powerful combat fighter than the Eagle Mk II, trading some agility for superior speed and firepower.",
        "modern_impact": "Ship review and release information for the pilot community.",
    },
    "10_the_truth_about_emperors_dawn.md": {
        "persons": [],
        "groups": ["Imperial Herald", "Emperor's Dawn"],
        "locations": [],
        "technologies": [],
        "summary": "Captured materials from Emperor's Dawn revealed the group's aims to destabilize Imperial society. While initially appearing to espouse traditional Imperial beliefs, the propaganda became increasingly sinister, denouncing the Emperor and demanding his removal so someone more fitting could take his place. No candidate has been named.",
        "player_impact": "Pilots fighting against Emperor's Dawn should understand that the group is not merely treasonous but seeks to fundamentally reshape Imperial society through violent means.",
        "modern_impact": "GalNet community report documenting current events in the galaxy.",
    },
    "11_emperors_dawn_bases_discovered.md": {
        "persons": ["Denton Patreus"],
        "groups": ["Imperial Navy", "Emperor's Dawn"],
        "locations": ["Dakshmandi", "Maausk"],
        "technologies": [],
        "summary": "Imperial intelligence discovered several bases belonging to Emperor's Dawn. Senator Denton Patreus launched a military campaign to destroy the insurrectionists, mobilizing Imperial forces and calling on independent pilots to aid the operation with generous rewards offered for contributions.",
        "player_impact": "Independent pilots can join Senator Patreus's campaign against Emperor's Dawn in the Dakshmandi and Maausk systems. Combat pilots will find opportunities to earn rewards while supporting the Empire.",
        "modern_impact": "GalNet community report documenting current events in the galaxy.",
    },
    "11_emperors_dawn_issues_request_for_supplies.md": {
        "persons": ["Denton Patreus"],
        "groups": ["Imperial Citizen", "Emperor's Dawn"],
        "locations": ["Ipilyaqa", "Ch'i Lin"],
        "technologies": [],
        "summary": "As Senator Patreus launched his military campaign against Emperor's Dawn, the insurgent group issued a public appeal for illegal commodities including progenitor cells and narcotics. Delivery points were established at starports in the Ipilyaqa and Ch'i Lin systems, with the Empire urging the public to ignore the request.",
        "player_impact": "Pilots should be aware that Emperor's Dawn is requesting illegal commodities at stations in Ipilyaqa and Ch'i Lin. Delivering to them would support a terrorist organization.",
        "modern_impact": "Trade initiative affecting commodity markets and local economies.",
    },
    "11_kumo_crew_to_target_lavigny_duval.md": {
        "persons": ["Archon Delaine"],
        "groups": ["Kumo Crew"],
        "locations": [],
        "technologies": [],
        "summary": "The Kumo Crew planned to target systems under Arissa Lavigny-Duval's influence, penetrating deeper into Imperial territory than ever before. The operation aimed to force Duval to admit the foolishness of the Pegasi War by bringing it close to home, representing a significant escalation from their previous Operation Uranus against Patreus's worlds.",
        "player_impact": "Pilots in systems under Lavigny-Duval's influence should be alert for increased Kumo Crew pirate activity. Combat pilots may find bounty hunting opportunities.",
        "modern_impact": "Highlights the humanitarian crisis in the Pegasi Sector and the challenges of protecting civilian populations during pirate wars.",
    },
    "11_the_peoples_princess_speaks.md": {
        "persons": ["Aisling Duval"],
        "groups": ["Imperial Herald"],
        "locations": ["Capitol"],
        "technologies": [],
        "summary": "At a public charity event where several dozen slaves were freed, Princess Aisling Duval claimed she was the natural heir to the Imperial throne as the closest living relative of Emperor Hengist Duval. Her attempt to gloss over the legal succession process sparked angry rebuttals from legal experts and rival candidates, though street polls showed near-universal public support for the Princess.",
        "player_impact": "None",
        "modern_impact": "GalNet community report documenting current events in the galaxy.",
    },
    "13_research_into_strange_objects_begins.md": {
        "persons": ["Ishmael Palin"],
        "groups": ["Homeland Scientific Council"],
        "locations": ["HIP 102128", "Tanmark", "Fort Harrison"],
        "technologies": ["Unknown Artefact", "Anomalous Extraterrestrial Object"],
        "summary": "Professor Ishmael Palin, formerly of the Homeland Scientific Council, was appointed to lead a Federal research programme studying strange objects discovered in systems including Tanmark and HIP 102128. The quasi-organic artefacts, dubbed AEOs, can damage nearby machinery including ship cargo holds and systems. Palin refused to speculate on their non-human origin, promising rigorous examination in the coming weeks.",
        "player_impact": "Pilots transporting unknown artefacts should be aware they can damage ship systems and cargo holds. The research into these mysterious objects may reveal important discoveries about non-human intelligence.",
        "modern_impact": "Advances understanding of the mysterious alien artefacts and their threat to station infrastructure.",
    },
    "14_imperial_slave_regulations_proposed.md": {
        "persons": ["Svetlana Zhukov"],
        "groups": ["Imperial Navy", "Imperial Senate", "Interstellar Press", "Imperial Slave Association"],
        "locations": ["Capitol"],
        "technologies": [],
        "summary": "Following a recent audit of the Imperial Slave Association, the Imperial Senate Audit Committee proposed new regulations for transporting Imperial slaves. The proposals include requiring pilots to hold Master rank in the Imperial Navy and setting aside resources to recover slaves transported outside the Empire. ISA chairwoman Svetlana Zhukov voiced support, though political commentators doubted the regulations would be approved.",
        "player_impact": "Pilots transporting Imperial slaves may soon need Master rank in the Imperial Navy. Be aware of proposed regulations that could affect slave trading operations and recovery requirements.",
        "modern_impact": "Ship review and release information for the pilot community.",
    },
    "15_senator_arissa_lavigny_duval_calls_impromptu_press_conference.md": {
        "persons": ["Arissa Lavigny-Duval"],
        "groups": ["Imperial Senate"],
        "locations": [],
        "technologies": [],
        "summary": "Senator Arissa Lavigny-Duval called an impromptu press conference after Senate deliberations, stating the Empire needs stability and continuity. She shared that Emperor Hengist Duval had shared a vision with her during his recovery. When asked if she considered herself the heir, she deferred to the Senate's decision while committing to work toward the Emperor's vision regardless of the outcome.",
        "player_impact": "None",
        "modern_impact": "Infrastructure project with long-term benefits for the affected region.",
    },
    "15_vice_presidents_investigation_data_found.md": {
        "persons": ["Nigel Smeaton"],
        "groups": ["Federal Times", "Sirius Corporation"],
        "locations": ["Sirius"],
        "technologies": [],
        "summary": "A concealed data chit was discovered among Vice President Nigel Smeaton's personal belongings. With help from Federal Times technicians, some encrypted information was extracted. The data may help locate the wreckage of the Highliner Antares and has been handed to Sirius Corporation and investigating officers. The family spokesman declined to answer questions.",
        "player_impact": "The discovery of Smeaton's data chit may lead to locating the Highliner Antares wreckage. Pilots should monitor developments in the Federal political crisis and the ongoing investigation.",
        "modern_impact": "Deepens the Federal political crisis around the Antares conspiracy and Vice President Smeaton's murder.",
    },
    "16_munshin_announces_plan_to_aid_refugees.md": {
        "persons": ["Quade"],
        "groups": ["Pilots Federation", "Libertas Cooperative"],
        "locations": ["Munshin", "Ocrinox's Orbiter", "Pegasi Sector"],
        "technologies": [],
        "summary": "Officials at Ocrinox's Orbiter announced plans to build a state-of-the-art resettlement facility for Pegasi Pirate War refugees. The plan leverages Munshin's distance from the war, available food and jobs, and supporting infrastructure. Officials also requested urgent medical supply deliveries from the Pilots Federation and Princess Aisling Duval.",
        "player_impact": "Pilots can deliver medical supplies to Ocrinox's Orbiter in the Munshin system to aid Pegasi Sector refugees. The humanitarian effort welcomes all transport-capable commanders.",
        "modern_impact": "Highlights the humanitarian crisis in the Pegasi Sector and the challenges of protecting civilian populations during pirate wars.",
    },
    "17_frontline_report_the_war_against_emperors_dawn.md": {
        "persons": ["Denton Patreus", "Anthony Corvus", "Katherine Ryder"],
        "groups": ["Imperial Herald", "Imperial Navy", "Emperor's Dawn"],
        "locations": ["Dakshmandi", "Maausk"],
        "technologies": [],
        "summary": "Journalist Katherine Ryder reported from the frontlines of Senator Patreus's campaign against Emperor's Dawn in the Dakshmandi and Maausk systems. General Anthony Corvus described the insurgents as disciplined and methodical, with morale that never wavers despite losses. Hundreds of independent pilots have joined the insurgents, and critics note Patreus may have underestimated the group's resolve, risking a protracted conflict that could exhaust Imperial resources.",
        "player_impact": "Combat pilots can participate in the war against Emperor's Dawn in Dakshmandi and Maausk. However, the conflict is proving more difficult than anticipated, with insurgents showing unexpected discipline and resolve.",
        "modern_impact": "Ship review and release information for the pilot community.",
    },
    "17_kumo_operation_to_hit_aisling_duval.md": {
        "persons": ["Archon Delaine", "Mikalus"],
        "groups": ["Kumo Crew"],
        "locations": [],
        "technologies": [],
        "summary": "Kumo Crew commanders swept across systems controlled by Arissa Lavigny-Duval, penetrating deeper than in any previous skirmish. Leaked intelligence indicated Archon Delaine would focus on planets and stations pledged to Aisling Duval. The operation elevated danger for Imperial citizens and demonstrated that the Pegasi Pirate War had taken on a new dimension, drawing on the strength and resources of a thousand worlds.",
        "player_impact": "Pilots in Aisling Duval's systems should prepare for increased Kumo Crew pirate activity. Combat pilots may find opportunities to defend Imperial systems and earn combat bonds.",
        "modern_impact": "Highlights the humanitarian crisis in the Pegasi Sector and the challenges of protecting civilian populations during pirate wars.",
    },
    "18_did_aisling_duval_know_about_emperors_dawn.md": {
        "persons": ["Aisling Duval", "Damon Clarke"],
        "groups": ["Imperial Herald", "D and C Shipping"],
        "locations": [],
        "technologies": [],
        "summary": "The Imperial Herald published an exposé alleging links between Princess Aisling Duval's inner council and Emperor's Dawn funding sources. While no direct connection to Aisling was alleged, patron and industrialist Damon Clarke's company, D and C Shipping, apparently funded weapon shipments to known Emperor's Dawn members three years ago. Clarke was unavailable for comment, with his company defending its legitimate shipping operations.",
        "player_impact": "The scandal has caused a dramatic fall in Aisling Duval's popularity polls. Pilots should monitor the situation as the Imperial Senate investigation unfolds and Clarke remains at large.",
        "modern_impact": "Ship review and release information for the pilot community.",
    },
    "18_hutton_mug_appeal_successful.md": {
        "persons": ["Chase Fulbright"],
        "groups": ["BlipMagnet"],
        "locations": ["Hutton Orbital", "Alpha Centauri"],
        "technologies": [],
        "summary": "BlipMagnet's Hutton Mug appeal proved highly successful, with thousands of independent pilots delivering scrap materials to Hutton Orbital. Director Chase Fulbright announced they had more than enough material for production but apologized for infrastructure delays. The commemorative mugs, made for pilots completing the epic 0.22 light year journey to Hutton Orbital, would be produced as soon as possible.",
        "player_impact": "Pilots who delivered scrap to Hutton Orbital can expect their commemorative Hutton Mug once production infrastructure issues are resolved. The journey to Hutton Orbital remains a popular badge of honor.",
        "modern_impact": "GalNet community report documenting current events in the galaxy.",
    },
    "18_imperial_internal_security_service_issues_another_appeal.md": {
        "persons": ["Cope"],
        "groups": ["Imperial Internal Security Service", "Cemiess Empire Party"],
        "locations": ["Cemiess", "Mackenzie Relay"],
        "technologies": [],
        "summary": "The Imperial Internal Security Service issued a second public appeal for exploration data, explicitly stating it would be used to locate Emperor's Dawn bases. Agent Cope authorized the Cemiess Empire Party to reimburse pilots delivering reliable exploration data to Mackenzie Relay in the Cemiess system, as part of efforts to neutralize the insurgent threat.",
        "player_impact": "Explorers can deliver exploration data to Mackenzie Relay in Cemiess to help the IISS locate Emperor's Dawn bases and earn reimbursement from the Cemiess Empire Party.",
        "modern_impact": "Notable exploration achievement expanding the boundaries of known space.",
    },
    "19_aisling_duval_issues_statement.md": {
        "persons": ["Aisling Duval", "Damon Clarke"],
        "groups": ["Imperial Herald", "Emperor's Dawn"],
        "locations": ["Cemiess"],
        "technologies": [],
        "summary": "Following revelations of alleged links between her office and Emperor's Dawn, Princess Aisling Duval issued a statement denying all knowledge of the connection. She announced an immediate internal investigation to root out disloyal staff. Popularity polls showed a dramatic fall for the 'People's Princess' as more details emerged. Patron Damon Clarke remained unavailable for comment, with reports suggesting he had fled the Empire.",
        "player_impact": "The Imperial Senate has launched an investigation into Aisling Duval's alleged links to Emperor's Dawn. Pilots should expect continued political turbulence as the succession crisis deepens.",
        "modern_impact": "Critical moment in the Imperial succession crisis, shaping the future leadership of the Empire.",
    },
    "19_local_faction_helps_ready_munshin.md": {
        "persons": ["Quade"],
        "groups": ["Libertas Cooperative"],
        "locations": ["Munshin", "Ocrinox's Orbiter", "Pegasi Sector"],
        "technologies": [],
        "summary": "The Libertas Cooperative, a group of freed Imperial slaves and their descendants, led resettlement efforts for Pegasi Sector refugees at Ocrinox's Orbiter. Members worked docking bays and unloading cargo while independent commanders increased medicine deliveries. The Munshin government praised their dedication, and the cooperative invited refugees to seek employment with them.",
        "player_impact": "Pilots can continue delivering medicines to Ocrinox's Orbiter in Munshin to support the refugee resettlement effort led by the Libertas Cooperative.",
        "modern_impact": "Highlights the humanitarian crisis in the Pegasi Sector and the challenges of protecting civilian populations during pirate wars.",
    },
    "20_federal_research_programme_terminated.md": {
        "persons": ["Ishmael Palin", "Aoishe Quaid"],
        "groups": [],
        "locations": ["Fort Harrison"],
        "technologies": ["Unknown Artefact", "Anomalous Extraterrestrial Object"],
        "summary": "The Federal research programme studying anomalous extraterrestrial objects was abruptly terminated by Fort Harrison station governor Aoishe Quaid only one week after its inauguration. Sources suggested Quaid was pressured into the decision despite her enthusiasm for the project. The quasi-organic objects, capable of broadcasting location data across vast distances, were considered the scientific find of the decade. Professor Ishmael Palin declined to comment.",
        "player_impact": "The termination of UA research raises questions about who is suppressing information about these mysterious artefacts. Pilots should be cautious when transporting unknown artefacts, which can damage ship systems.",
        "modern_impact": "Advances understanding of the mysterious alien artefacts and their threat to station infrastructure.",
    },
    "20_senator_patreus_calls_for_senate_investigation.md": {
        "persons": ["Denton Patreus", "Damon Clarke"],
        "groups": ["Imperial Herald", "Imperial Senate"],
        "locations": [],
        "technologies": [],
        "summary": "Senator Denton Patreus called for a full Senate investigation into reported links between Emperor's Dawn and Princess Aisling Duval's office. Drawing on his own experience when a household member committed a heinous act, Patreus demanded immediate action. No new facts were released regarding patron Damon Clarke, who was believed to have fled the Empire.",
        "player_impact": "None",
        "modern_impact": "GalNet community report documenting current events in the galaxy.",
    },
    "21_chancellor_blaine_confirms_senate_investigation.md": {
        "persons": ["Anders Blaine", "Aisling Duval", "Damon Clarke"],
        "groups": ["Imperial Senate", "Imperial Internal Security Service"],
        "locations": [],
        "technologies": [],
        "summary": "Chancellor Anders Blaine confirmed a Senate investigation into the connection between Princess Aisling Duval's office and Emperor's Dawn would begin immediately, despite the Senate being in closed session until the succession is decided. Aisling stated she would fully comply and had discovered alarming information to share. Several of Damon Clarke's associates were arrested and questioned by the IISS.",
        "player_impact": "None",
        "modern_impact": "GalNet community report documenting current events in the galaxy.",
    },
    "22_a_galactic_treasure_hunt.md": {
        "persons": ["Alfred Jeffress"],
        "groups": [],
        "locations": [],
        "technologies": [],
        "summary": "Reclusive philanthropist Alfred Jeffress announced a galaxy-wide treasure hunt with a share of his fortune as the prize. A mystery object was hidden somewhere in space, with a riddle offered as the only clue: 'A vision of the Devil and Orion's hounds will start you on your path.' Hundreds of pilots immediately began searching for the object.",
        "player_impact": "Pilots can participate in the galactic treasure hunt by solving Alfred Jeffress's riddle and searching for the hidden mystery object. The first to find it and deliver it to the specified location wins a share of Jeffress's fortune.",
        "modern_impact": "Community-driven treasure hunt engaging independent pilots in puzzle-solving across the galaxy.",
    },
    "22_aisling_duval_praises_the_munshin_system.md": {
        "persons": ["Aisling Duval", "Quade"],
        "groups": ["Imperial Navy", "Libertas Cooperative"],
        "locations": ["Munshin", "Ocrinox's Orbiter"],
        "technologies": [],
        "summary": "Princess Aisling Duval praised relief workers in the Munshin system, calling them true examples of Imperial citizenship and heroes. She extended gratitude to the Libertas Cooperative and commanders delivering medicines to Ocrinox's Orbiter. Critics immediately accused her of overlooking Imperial Navy pilots killed in the Pegasi Pirate War, questioning where her support was for their families.",
        "player_impact": "Pilots continuing to deliver medicines to Ocrinox's Orbiter are recognized by Princess Aisling Duval for their humanitarian efforts. However, the praise has drawn criticism from those supporting the military effort in the Pegasi Sector.",
        "modern_impact": "Highlights the humanitarian crisis in the Pegasi Sector and the challenges of protecting civilian populations during pirate wars.",
    },
    "22_shelter_from_the_storm.md": {
        "persons": ["Adric Claavis", "Gan"],
        "groups": ["Utopia", "Kumo Crew"],
        "locations": ["Munshin"],
        "technologies": [],
        "summary": "Utopia joined the Munshin government's call for help with Pegasi Pirate War refugees. Adjudicator Adric Claavis announced Utopia would deliver humanitarian supplies and welcome refugees seeking new lives on Utopian worlds. Utopian ambassadors requested passage through Kumo Crew space to reach Munshin, marking an unusual diplomatic overture to the pirates.",
        "player_impact": "Pilots can support the humanitarian effort by delivering supplies to Munshin. Utopia's involvement expands the relief network for Pegasi Sector refugees.",
        "modern_impact": "Highlights the humanitarian crisis in the Pegasi Sector and the challenges of protecting civilian populations during pirate wars.",
    },
    "23_pirates_target_pegasi_refugees.md": {
        "persons": ["Quade"],
        "groups": ["Defence Force of Amitrite", "Kumo Crew"],
        "locations": ["Amitrite", "Pegasi Sector"],
        "technologies": [],
        "summary": "Pirates attacked refugees fleeing the Pegasi Pirate War in the Amitrite system. The overloaded and poorly equipped transports were easy prey, with families carrying prized possessions making them particularly attractive targets. The Defence Force of Amitrite warned their forces were stretched too thin and urged refugees to avoid the system or fly in convoys.",
        "player_impact": "Combat pilots can help protect refugees in Amitrite by eliminating pirates. Bounty hunting in Amitrite is encouraged to reduce the threat to vulnerable refugee transports.",
        "modern_impact": "Highlights the humanitarian crisis in the Pegasi Sector and the challenges of protecting civilian populations during pirate wars.",
    },
    "25_pirates_continue_to_target_refugees.md": {
        "persons": [],
        "groups": ["Defence Force of Amitrite", "Imperial Navy"],
        "locations": ["Amitrite", "Munshin"],
        "technologies": [],
        "summary": "Pirates continued targeting refugees in Amitrite as transports stopped to refuel while traveling to the Munshin resettlement centre. In response, the Imperial Navy and Defence Force of Amitrite issued bounties on pirates, encouraging independent pilots with combat experience to help protect the vulnerable refugee convoys.",
        "player_impact": "Combat pilots can earn bounties in Amitrite by eliminating pirates targeting refugee transports. Protecting the convoys ensures safe passage for families fleeing the Pegasi Pirate War to Munshin.",
        "modern_impact": "Highlights the humanitarian crisis in the Pegasi Sector and the challenges of protecting civilian populations during pirate wars.",
    },
    "25_senator_patreus_offers_support_to_senator_lavigny_duval.md": {
        "persons": ["Denton Patreus", "Arissa Lavigny-Duval", "Anders Blaine", "Zemina Torval"],
        "groups": ["Imperial Senate"],
        "locations": [],
        "technologies": [],
        "summary": "Senator Denton Patreus publicly declared his support for Arissa Lavigny-Duval as Emperor, despite being a potential candidate himself. He praised her as the person who would already occupy the throne but for the Emperor's murder. The declaration followed Chancellor Blaine's existing support and Senator Torval's backing, significantly strengthening Lavigny-Duval's position as Aisling Duval's popularity fell due to the Emperor's Dawn scandal.",
        "player_impact": "None",
        "modern_impact": "GalNet community report documenting current events in the galaxy.",
    },
    "25_sothis_crystalline_gold.md": {
        "persons": [],
        "groups": [],
        "locations": ["Sothis", "Newholm Station"],
        "technologies": ["Sothis Crystalline Gold"],
        "summary": "Scientists at Newholm Station in the Sothis system discovered a new metalloid called Sothis Crystalline Gold, produced by exposing ordinary gold to thermal vent gases on planets Sothis A5 and A6. The transformation process is not fully understood, but the resultant metal is completely unique. Scientists are offering pilots quantities of the rare material in exchange for delivering gold to Newholm Station for further testing.",
        "player_impact": "Pilots can deliver gold to Newholm Station in the Sothis system to receive Sothis Crystalline Gold and help scientists conduct further tests on this unique new material.",
        "modern_impact": "Notable exploration achievement expanding the boundaries of known space.",
    },
    "27_palin_invited_to_join_research_group.md": {
        "persons": ["Ishmael Palin", "Lord Zoltan"],
        "groups": ["Canonn Interstellar Research Group"],
        "locations": ["Varati"],
        "technologies": ["Unknown Artefact"],
        "summary": "Following the termination of Professor Ishmael Palin's Federal research programme into unknown artefacts, the Canonn Interstellar Research Group invited him to join their independent scientific body. The Canonn expressed suspicion that someone in power was suppressing UA research and vowed to redouble their open research efforts. They offered to assemble a quick-response team to assure Palin's safety.",
        "player_impact": "The Canonn's invitation to Professor Palin suggests significant pressure to suppress UA research. Pilots interested in the mystery of unknown artefacts should follow the Canonn's research efforts and consider supporting independent scientific investigation.",
        "modern_impact": "Advances understanding of the mysterious alien artefacts and their threat to station infrastructure.",
    },
    "28_plastic_fantastic.md": {
        "persons": ["Rubbernuke"],
        "groups": [],
        "locations": [],
        "technologies": [],
        "summary": "Bobbleheads are returning to cockpits after being banned for over a year due to their involvement in thousands of accidents and even pirate murders. After intense lobbying from pilot groups and toy manufacturers, a new generation is being produced. Security services released safety advice reminding pilots to check Bobbleheads for explosives, hidden cameras, and illicit drugs, and to ensure they are firmly affixed before maneuvers.",
        "player_impact": "Pilots can once again acquire Bobbleheads for their cockpits. Ensure they are properly secured and checked for any hidden dangers before flight operations.",
        "modern_impact": "Pilot safety initiative with potential regulatory implications for starship design.",
    },
    "28_senator_arissa_lavigny_duval_gains_more_powerful_support.md": {
        "persons": ["Arissa Lavigny-Duval", "Denton Patreus", "Anders Blaine", "Zemina Torval", "Aisling Duval"],
        "groups": ["Imperial Herald", "Imperial Senate", "Emperor's Dawn"],
        "locations": ["Capitol", "Denton"],
        "technologies": [],
        "summary": "Senator Arissa Lavigny-Duval consolidated her position as the frontrunner for Emperor following Senator Patreus's public endorsement. She already enjoyed Chancellor Blaine's support, and Senator Torval's backing further strengthened her claim. The Imperial Herald's revelations about Aisling Duval's alleged links to Emperor's Dawn severely damaged the Princess's ratings and Senate support.",
        "player_impact": "The Imperial succession is consolidating around Arissa Lavigny-Duval. Pilots should expect the Senate to reach a decision soon, with significant implications for Imperial policy and power dynamics.",
        "modern_impact": "Critical moment in the Imperial succession crisis, shaping the future leadership of the Empire.",
    },
    "28_shadow_president_winters_calls_for_investigation.md": {
        "persons": ["Felicia Winters", "Nigel Smeaton"],
        "groups": ["Federal Congress", "Federal Times"],
        "locations": ["Sol", "Mars"],
        "technologies": [],
        "summary": "Shadow President Felicia Winters called for an open and thorough investigation into the Federal Times allegations about Vice President Nigel Smeaton's murder. Speaking before Congress, Winters stated there was too much evidence to ignore and called on President Hudson to immediately instigate an impartial investigation. Her speech received support from both sides of the political divide, though the President's office had not yet responded.",
        "player_impact": "The Federal political crisis deepens as Winters demands an open investigation into Smeaton's murder and the Antares conspiracy. Pilots should monitor Federal developments for potential shifts in policy and power.",
        "modern_impact": "Deepens the Federal political crisis around the Antares conspiracy and Vice President Smeaton's murder.",
    },
    "29_pirates_wiped_out_in_amitrite.md": {
        "persons": ["Quade"],
        "groups": ["Defence Force of Amitrite", "Libertas Cooperative"],
        "locations": ["Amitrite", "Munshin", "Pegasi Sector"],
        "technologies": [],
        "summary": "Independent pilots helped the Defence Force of Amitrite clear the system of pirates, eliminating hundreds of hostile ships and driving crime to new lows. The Libertas Cooperative thanked pilots on behalf of Pegasi Sector refugees, noting that families separated by the war could now be reunited safely. Some media speculated the high participation was due to Arissa Lavigny-Duval's crime-deterrence policies, which the DFA dismissed as crass.",
        "player_impact": "Combat pilots successfully cleared Amitrite of pirates, making the refugee route to Munshin safer. Continue supporting anti-piracy efforts in systems along the refugee corridor.",
        "modern_impact": "Highlights the humanitarian crisis in the Pegasi Sector and the challenges of protecting civilian populations during pirate wars.",
    },
    "29_president_hudson_confirms_investigation.md": {
        "persons": ["Zachary Hudson", "Felicia Winters"],
        "groups": ["Federal Security Service", "Federal Times"],
        "locations": ["Sol", "Mars", "White House"],
        "technologies": [],
        "summary": "President Hudson responded to Shadow President Winters's call for an investigation into the Federal Times allegations. At a White House press conference, he instructed agencies to pursue the evidence, promising wrongdoers would be prosecuted if allegations proved true. The Federal Security Service was named lead agency. Winters responded by noting Hudson was ignoring the call for an open investigation.",
        "player_impact": "The Federal Security Service is now leading the investigation into the Antares conspiracy and Smeaton's murder. Pilots should watch for developments as the Federal political crisis continues to unfold.",
        "modern_impact": "Deepens the Federal political crisis around the Antares conspiracy and Vice President Smeaton's murder.",
    },
    "30_emperors_dawn_appeal_meets_with_mixed_response.md": {
        "persons": [],
        "groups": ["Emperor's Dawn"],
        "locations": [],
        "technologies": [],
        "summary": "Emperor's Dawn's public appeal for progenitor cells and narcotics received a mixed response. While those opposing the Empire were eager to help, many independent traders found supporting a known enemy unthinkable. The request for progenitor cells succeeded, but the narcotics request failed, reflecting the divided attitude toward the insurgent group. The impact on Emperor's Dawn's future capabilities remains uncertain.",
        "player_impact": "The mixed response to Emperor's Dawn's supply appeal suggests the group may face resource constraints. Pilots should continue monitoring the conflict and supporting Imperial forces where possible.",
        "modern_impact": "Critical moment in the Imperial succession crisis, shaping the future leadership of the Empire.",
    },
}


def parse_frontmatter(text):
    m = re.match(r'^---\n(.*?)\n---\n', text, re.DOTALL)
    if not m:
        return None, text
    try:
        fm = yaml.safe_load(m.group(1))
        body = text[m.end():]
        return fm, body
    except Exception as e:
        print(f"YAML parse error: {e}")
        return None, text


def quote_if_needed(val):
    """Quote strings containing colons to avoid YAML parsing issues."""
    if isinstance(val, str) and ':' in val:
        return f'"{val}"'
    return val


def dump_yaml_value(key, val, indent=0):
    """Custom YAML dumper for our specific needs."""
    prefix = "  " * indent
    if val is None:
        return f"{prefix}{key}:"
    if isinstance(val, bool):
        return f"{prefix}{key}: {str(val).lower()}"
    if isinstance(val, int):
        return f"{prefix}{key}: {val}"
    if isinstance(val, str):
        q = quote_if_needed(val)
        if q != val:
            return f'{prefix}{key}: {q}'
        # Multiline strings
        if '\n' in val:
            lines = val.split('\n')
            return f"{prefix}{key}: |\n" + "\n".join(f"{prefix}  {l}" for l in lines)
        return f"{prefix}{key}: {val}"
    if isinstance(val, list):
        if not val:
            return f"{prefix}{key}: []"
        lines = [f"{prefix}{key}:"]
        for item in val:
            q = quote_if_needed(item)
            lines.append(f"{prefix}- {q}")
        return "\n".join(lines)
    return f"{prefix}{key}: {val}"


def build_frontmatter(fm):
    """Build frontmatter string preserving order and handling special cases."""
    # Define field order
    field_order = [
        "uuid", "title", "slug", "date", "source",
        "persons", "groups", "locations", "technologies",
        "topics", "arc_id", "arc_chapter",
        "summary", "player_impact", "modern_impact",
        "legacy_weight", "significance"
    ]
    lines = ["---"]
    for key in field_order:
        if key in fm:
            dumped = dump_yaml_value(key, fm[key])
            if "\n" in dumped:
                lines.append(dumped)
            else:
                lines.append(dumped)
    # Add any remaining fields not in order
    for key in fm:
        if key not in field_order:
            lines.append(dump_yaml_value(key, fm[key]))
    lines.append("---")
    return "\n".join(lines)


def process_file(filename, enrich):
    path = DIR / filename
    with open(path, 'r') as f:
        text = f.read()

    fm, body = parse_frontmatter(text)
    if fm is None:
        print(f"SKIP {filename}: could not parse frontmatter")
        return

    # Remove old entities field (often contains sentence fragments)
    if "entities" in fm:
        del fm["entities"]

    # Update with enrichment data
    for key, val in enrich.items():
        if key == "persons" and not val:
            # Keep existing persons if enrichment doesn't specify any
            pass
        elif val is not None:
            fm[key] = val

    new_fm = build_frontmatter(fm)
    new_text = new_fm + "\n" + body

    with open(path, 'w') as f:
        f.write(new_text)
    print(f"OK {filename}")


def main():
    for filename, enrich in ENRICHMENTS.items():
        process_file(filename, enrich)


if __name__ == "__main__":
    main()
