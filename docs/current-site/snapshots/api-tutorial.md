<!-- Verbatim snapshot of https://api.opengwas.io/api/ taken 2026-11-02 for the redesign. Converted from HTML to Markdown; wording unchanged. Do not treat as current terms. -->

![](/static/images/logo/opengwas/text-white.png)

### System status and maintenance schedule

To check system status, visit:  
</api/status> (throttle applies)

To check uptime and maintenance schedule, visit:  
<https://status.opengwas.io>

[API Documentation](/api/docs)
[OpenGWAS Website](https://opengwas.io)

---

### Overview

This is a RESTful API for programmatic access to the IEU OpenGWAS database. The API is designed to support the following operations:

- Make available study information about all the GWAS datasets in the database
- Obtain the top hits from a GWAS, with optional automatic clumping.
- Find any set of variant-trait associations based on rsid or chromosome:position.
- Automatically find LD proxies if a variant is missing from a GWAS database.
- Calculate LD matrices across a set of variants.
- Phenome-wide association study (PheWAS) - Perform fast lookups of a particular variant across all datasets.
- Get [dbSNP](https://www.ncbi.nlm.nih.gov/snp/) information and annotations on a set of variants.

The API can be used directly by your applications, or accessed through convenient packages in R and Python. More information on those below. The [TwoSampleMR](https://github.com/MRCIEU/TwoSampleMR) R package, and [MR-Base](http://www.mrbase.org/) web apps both use this API in order to automatically perform Mendelian randomization for causal inference. The [gwasglue](https://mrcieu.github.io/gwasglue/) R package aims to extend the use of these data to further types of statistical methods.

---

### Authentication

| **Endpoint** | **Authentication** |
| --- | --- |
| /status, /batches | None |
| All other endpoints | JWT (required) |

---

##### JSON Web Token (JWT)

You need to prove your identity (authenticate) to use our service, even if you are querying a public dataset.

JSON Web Token (JWT) is used for authentication. The token is required for most endpoints. To obtain a token, sign in to the [account](https://api.opengwas.io/profile) page. You will be prompted to generate a token which is valid for 14 days.

---

##### If you are using packages developed by us

The ieugwasr and ieugwaspy packages are updated regularly to keep abreast of the changes of OpenGWAS API. If you use ieugwasr or TwoSampleMR etc. (which depends on ieugwasr), read [ieugwasr tutorial](https://mrcieu.github.io/ieugwasr/articles/guide.html#authentication) about how to set up JWT. For ieugwaspy, refer to the [ieugwaspy docs](https://mrcieu.github.io/ieugwaspy/api.html).

---

##### If you are building you own packages

The [API documentation](/api/docs) provides a list of endpoints, whether they are protected (require authentication), the parameters and responses, and an interactive way to try out. To try the protected endpoints, click the green 'Authorize' button in API docs and provide your token as instructed.

*IMPORTANT - In either circumstances below you must cite OpenGWAS properly - OpenGWAS must not be provided as "white label" software or service by any means.*

(1) If you package depends on ieugwasr or ieugwaspy, make sure your end users are aware of OpenGWAS JWT, preferably by including a link to this page in your product docs.

(2) If you are building from scratch i.e. writing your own code to make API calls to OpenGWAS, in addition to (1), you also need to implement something that adds JWT into the request header under the key `Authorization` with value `Bearer your_token`. Note that there is a whitespace between `Bearer` and your token.

You may want to visit the [API docs](/api/docs) and find the `/user` endpoint, which is created to help you validate your implementation of the authentication process.
  
- **What will happen without a valid token?**  
If you just click 'Try it out' then 'Execute', you will get a '401 Unauthorized' error.
  
- **What if I have a valid token?**  
If you focus on the upper right corner of the /user area, you will see a lock icon. Click the lock icon and you will find 'token\_jwt' as available authorizations. Follow the instruction, click 'Authorize', and finally try to execute on the /user endpoint again. This time you will get '200 OK' and you can see your user information in the response body.
  
- **Is there any other error?**  
Yes. You may see other errors (e.g. if you go beyond the rate limit you will get the '429 Too Many Requests' error), so when you are using the 200 status code as the indication of success, you may also want to check the response body.

---

### Allowance and cost

##### Allowance (free credits)

As part of our fair use policy, users will be given allowance for the cost of the requests they make in each time span. The allowance is provided free of charge.

The allowance is reset periodically and the clock starts at your first request. E.g. if the allowance is "1000 per 10 minutes" and you made your first request at 09:41:19, your allowance will be reset to 1000 at 09:51:19. Your real-time allowance information is available on your [account](https://api.opengwas.io/profile) page, or in the response header (X-Allowance-\* and Retry-After) of every request, except for those endpoints of which the cost is 0.

Resetting your token (JWT) will not reset your allowance. If you have run out of allowance, you have to wait until the next period. If you insist sending requests and accumulate '429 Too Many Requests' errors, you account and IP address may be blocked for up to a week.

What's my allowance?

After your first sign-in you will be in the 'Trial' tier which only offers limited allowance. Please follow the instructions on you account page to upgrade you account to Standard.

| **User tier** | **Allowance (free credits)** |
| --- | --- |
| No allowance | 0 per 10 minutes |
| Trial | 100000 per 10 minutes |
| Standard | 100000 per 10 minutes |
| Commercial | 100000 per 10 minutes |

Note: University of Bristol users (who signed in using Microsoft, GitHub or email verification, as long as the email address on your OpenGWAS profile ends with @bristol.ac.uk) will be given higher (but not unlimited) allowance than displayed above. Please check your [account](https://api.opengwas.io/profile) page for details.

Read our [blog post](https://blog.opengwas.io/posts/user-auth-spring-2024/) for more info.

##### Cost (per request)

| **Endpoint** | **Cost per request** | **Conditions and notes** |
| --- | --- | --- |
| /status, /batches, /users | 0 (no cost, but still subject to fair-use policy) |  |
| /gwasinfo  /gwasinfo/files | 1 50 Nid × 1000 | 1 ≤ Nid ≤ 100 100 < Nid or no id is specified |
| /associations | max(Nid, Nvariant) max(Nid, Nvariant) × 5 | proxies = 1 |
| /tophits | Nid Nid × 10 Nid × 30 | clump = 1 (use preclumped data) clump = 0 (return all records) clump = 1 (requires new clumping) |
| /ld/clump /ld/matrix /ld/reflookup | 12 18 2 |  |
| /phewas | (Nvariant\_rsid + Nvariant\_chrpos + Nvariant\_cprange) × 20 + Nresults |  |
| /variants /variants/afl2/snplist | 1 10 |  |

---

### Related tools

For ease of use we have developed two packages which are solely designed to create easy interfaces to the API endpoints:

- The ieugwasr R package [[link]](https://mrcieu.github.io/ieugwasr)
- The ieugwaspy python package [[link]](https://github.com/mrcieu/ieugwaspy)

The following packages also connect to these data:

- The TwoSampleMR R package automatically performs Mendelian randomization on the data accessed through the API [[link]](https://github.com/mrcieu/TwoSampleMR)
- The gwasglue R packages connects the data to several other analytical tools related to e.g. colocalisation, fine mapping, etc [[link]](https://mrcieu.github.io/gwasglue/)
- The <https://opengwas.io> page provides an interactive way to browse through the available datasets.

---
