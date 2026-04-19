from datetime import datetime

def tailor_resume(job):
    """Generate ATS-optimized bullets based on job"""
    desc = job['description'].lower()
    bullets = []
    
    # Core achievements - always include
    bullets.append("• Engineered 15% increase in shift effectiveness through implementation of Lean Six Sigma methodologies and systematic root cause analysis")
    bullets.append("• Achieved zero Lost Time Injuries (LTIs) over 24-month period by championing OHSA compliance and JHSC safety initiatives")
    bullets.append("• Resolved 90% of labor disputes through collaborative engagement, maintaining production continuity for 45+ unionized personnel")
    
    # Tailored additions
    if 'weld' in desc or 'cwb' in desc or 'tssa' in desc:
        bullets.append("• Directed welding and fabrication operations as certified TSSA (1G-6G) and CWB Welding Inspector, ensuring 100% code compliance")
    
    if 'lean' in desc or 'six sigma' in desc or 'continuous' in desc:
        bullets.append("• Led continuous improvement initiatives resulting in 12% waste reduction and $2M capacity expansion support")
    
    if 'iso' in desc or 'quality' in desc or 'iatf' in desc:
        bullets.append("• Ensured 100% adherence to ISO 9001/IATF 16949 quality management systems through rigorous process audits")
    
    if 'automotive' in desc:
        bullets.append("• Managed high-volume automotive production lines with focus on JIT delivery and quality standards")
    
    if 'aerospace' in desc:
        bullets.append("• Applied AS9100 aerospace standards in precision manufacturing environment")
    
    return '\n'.join(bullets[:5])

def generate_cover_letter(company, title):
    today = datetime.now().strftime('%B %d, %Y')
    
    return f"""Raouf Mayahi
York, Ontario
(416) 897-7889 | raoufmayahi@gmail.com | linkedin.com/in/raoufmayahi

{today}

Hiring Manager
{company}
Ontario, Canada

Dear Hiring Manager,

RE: Application for {title} Position

I am writing to express my strong interest in the {title} position at {company}. With over 14 years of progressive leadership experience in heavy manufacturing, custom fabrication, and high-precision assembly operations, I offer a proven track record of driving operational excellence, cultivating safety-first cultures, and delivering quantifiable productivity improvements in unionized environments.

In my current capacity as Production Supervisor at Active Dynamics, I provide strategic leadership to a team of 45+ unionized professionals across multi-shift manufacturing operations. Through the disciplined application of Lean Six Sigma principles and comprehensive root cause analysis, I successfully engineered a 15% improvement in shift effectiveness while simultaneously achieving zero Lost Time Injuries over a consecutive 24-month period. This dual achievement underscores my commitment to balancing productivity objectives with uncompromising safety standards.

My approach to labor relations has been instrumental in maintaining operational stability. By fostering transparent communication and implementing collaborative problem-solving frameworks, I have successfully resolved 90% of labor disputes at the supervisory level, thereby preserving production schedules and enhancing team cohesion. This experience has equipped me with the nuanced understanding of union dynamics essential for effective manufacturing leadership.

My technical qualifications include TSSA certification (1G through 6G classifications), CWB Level 2 Welding Inspector certification, and extensive training in Lean Manufacturing, Six Sigma methodologies, and JHSC/OHSA regulatory compliance. During my tenure at Howden Canada, I maintained 100% adherence to ISO quality management systems while playing a pivotal role in supporting a 12% facility capacity expansion through optimized material procurement strategies and waste reduction initiatives.

{company}'s reputation for manufacturing excellence and commitment to continuous improvement aligns directly with my professional philosophy and career objectives. I am particularly impressed by your organization's focus on operational innovation and would welcome the opportunity to contribute my expertise in process optimization, HSE leadership, and team development to support your strategic goals.

I am confident that my combination of hands-on technical expertise, proven leadership capabilities, and dedication to operational excellence would make me a valuable addition to your manufacturing team. I would appreciate the opportunity to discuss how my background and achievements can contribute to {company}'s continued success.

Thank you for your time and consideration. I look forward to speaking with you soon.

Sincerely,

Raouf Mayahi

Enclosures: Resume
"""