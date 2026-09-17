--
-- PostgreSQL database dump
--

\restrict BfkigsQ2bOO2netHBf93FfWUCaWZob4ytya85NZDre75fsczetBcCvuXiUm5yLp

-- Dumped from database version 18.0
-- Dumped by pg_dump version 18.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: btree_gist; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS btree_gist WITH SCHEMA public;


--
-- Name: EXTENSION btree_gist; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION btree_gist IS 'support for indexing common datatypes in GiST';


--
-- Name: enforce_contribution_same_website(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.enforce_contribution_same_website() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_member_website_id VARCHAR;
    v_page_website_id   VARCHAR;
BEGIN
    SELECT website_id
    INTO v_member_website_id
    FROM public.website_member
    WHERE member_id = NEW.member_id;

    SELECT website_id
    INTO v_page_website_id
    FROM public.page
    WHERE page_id = NEW.page_id;

    IF v_member_website_id IS NULL THEN
        RAISE EXCEPTION
            'Contribution references unknown member_id: %',
            NEW.member_id;
    END IF;

    IF v_page_website_id IS NULL THEN
        RAISE EXCEPTION
            'Contribution references unknown page_id: %',
            NEW.page_id;
    END IF;

    IF v_member_website_id IS DISTINCT FROM v_page_website_id THEN
        RAISE EXCEPTION
            'Contribution Website mismatch: member % belongs to %, page % belongs to %',
            NEW.member_id,
            v_member_website_id,
            NEW.page_id,
            v_page_website_id;
    END IF;

    RETURN NEW;
END;
$$;


--
-- Name: enforce_refund_provenance(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.enforce_refund_provenance() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.event_type = 'payment_refunded' THEN

        IF NOT EXISTS (
            SELECT 1
            FROM public.payment_refund_activity_event p
            WHERE p.payment_ref = NEW.original_payment_ref
              AND p.event_type = 'payment_succeeded'
              AND p.account_id = NEW.account_id
              AND p.event_time < NEW.event_time
        ) THEN
            RAISE EXCEPTION
                'Invalid refund provenance: original_payment_ref % must reference an earlier payment_succeeded for Account %',
                NEW.original_payment_ref,
                NEW.account_id;
        END IF;

    END IF;

    RETURN NEW;
END;
$$;


--
-- Name: guard_contribution_parent_website_change(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.guard_contribution_parent_website_change() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF TG_TABLE_NAME = 'website_member' THEN

        IF EXISTS (
            SELECT 1
            FROM public.comment c
            JOIN public.page p
              ON p.page_id = c.page_id
            WHERE c.member_id = OLD.member_id
              AND p.website_id IS DISTINCT FROM NEW.website_id
        )
        OR EXISTS (
            SELECT 1
            FROM public.rating r
            JOIN public.page p
              ON p.page_id = r.page_id
            WHERE r.member_id = OLD.member_id
              AND p.website_id IS DISTINCT FROM NEW.website_id
        ) THEN
            RAISE EXCEPTION
                'Cannot move member % to Website %: existing contribution would become inconsistent',
                OLD.member_id,
                NEW.website_id;
        END IF;

    ELSIF TG_TABLE_NAME = 'page' THEN

        IF EXISTS (
            SELECT 1
            FROM public.comment c
            JOIN public.website_member m
              ON m.member_id = c.member_id
            WHERE c.page_id = OLD.page_id
              AND m.website_id IS DISTINCT FROM NEW.website_id
        )
        OR EXISTS (
            SELECT 1
            FROM public.rating r
            JOIN public.website_member m
              ON m.member_id = r.member_id
            WHERE r.page_id = OLD.page_id
              AND m.website_id IS DISTINCT FROM NEW.website_id
        ) THEN
            RAISE EXCEPTION
                'Cannot move page % to Website %: existing contribution would become inconsistent',
                OLD.page_id,
                NEW.website_id;
        END IF;

    END IF;

    RETURN NEW;
END;
$$;


--
-- Name: guard_refunded_payment_mutation(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.guard_refunded_payment_mutation() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF OLD.payment_ref IS NOT NULL
       AND EXISTS (
           SELECT 1
           FROM public.payment_refund_activity_event r
           WHERE r.event_type = 'payment_refunded'
             AND r.original_payment_ref = OLD.payment_ref
       )
    THEN
        IF NEW.payment_ref IS DISTINCT FROM OLD.payment_ref
           OR NEW.event_type <> 'payment_succeeded'
           OR EXISTS (
               SELECT 1
               FROM public.payment_refund_activity_event r
               WHERE r.event_type = 'payment_refunded'
                 AND r.original_payment_ref = OLD.payment_ref
                 AND (
                      r.account_id IS DISTINCT FROM NEW.account_id
                      OR NEW.event_time >= r.event_time
                 )
           )
        THEN
            RAISE EXCEPTION
                'Cannot modify payment %: existing Refund provenance would become invalid',
                OLD.payment_ref;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: account; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.account (
    account_id character varying(10) NOT NULL
);


--
-- Name: account_lifecycle_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.account_lifecycle_event (
    event_id character varying(14) NOT NULL,
    account_id character varying(10) NOT NULL,
    event_type character varying(20) NOT NULL,
    event_time timestamp with time zone NOT NULL,
    CONSTRAINT chk_account_lifecycle_event_type CHECK (((event_type)::text = ANY ((ARRAY['account_created'::character varying, 'account_closure'::character varying])::text[])))
);


--
-- Name: account_lifecycle_period; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.account_lifecycle_period (
    account_lifecycle_period_id character varying(11) NOT NULL,
    account_id character varying(10) NOT NULL,
    lifecycle_state character varying(10) NOT NULL,
    valid_from timestamp with time zone NOT NULL,
    valid_to timestamp with time zone,
    CONSTRAINT chk_account_lifecycle_period_dates CHECK (((valid_to IS NULL) OR (valid_to > valid_from))),
    CONSTRAINT chk_account_lifecycle_state CHECK (((lifecycle_state)::text = ANY ((ARRAY['active'::character varying, 'closed'::character varying])::text[])))
);


--
-- Name: acquisition_source_attribution; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.acquisition_source_attribution (
    signup_journey_id character varying(9) NOT NULL,
    acquisition_source character varying(20) NOT NULL,
    CONSTRAINT chk_acquisition_source CHECK (((acquisition_source)::text = ANY ((ARRAY['search'::character varying, 'direct'::character varying, 'social'::character varying, 'referral'::character varying])::text[])))
);


--
-- Name: audience_interaction_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audience_interaction_event (
    event_id character varying(17) NOT NULL,
    event_type character varying(30) NOT NULL,
    event_time timestamp with time zone NOT NULL,
    session_id character varying(13) NOT NULL,
    page_id character varying(13),
    content_item_id character varying(13),
    interaction_target_ref text,
    CONSTRAINT chk_audience_interaction_event_type CHECK (((event_type)::text = ANY ((ARRAY['page_viewed'::character varying, 'link_clicked'::character varying, 'video_watched'::character varying, 'file_downloaded'::character varying, 'form_started'::character varying, 'form_submitted'::character varying, 'search_performed'::character varying, 'search_result_clicked'::character varying, 'failure_friction'::character varying])::text[])))
);


--
-- Name: audience_session; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audience_session (
    session_id character varying(13) NOT NULL,
    visitor_id character varying(12) NOT NULL,
    website_id character varying(11) NOT NULL
);


--
-- Name: billing_cycle_period; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.billing_cycle_period (
    billing_cycle_period_id character varying(12) NOT NULL,
    account_id character varying(10) NOT NULL,
    billing_cycle character varying(10) NOT NULL,
    valid_from timestamp with time zone NOT NULL,
    valid_to timestamp with time zone,
    CONSTRAINT chk_billing_cycle_period_cycle CHECK (((billing_cycle)::text = ANY ((ARRAY['monthly'::character varying, 'annual'::character varying])::text[]))),
    CONSTRAINT chk_billing_cycle_period_dates CHECK (((valid_to IS NULL) OR (valid_to > valid_from)))
);


--
-- Name: comment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.comment (
    comment_id character varying(12) NOT NULL,
    member_id character varying(12) NOT NULL,
    page_id character varying(13) NOT NULL
);


--
-- Name: comment_lifecycle_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.comment_lifecycle_event (
    event_id character varying(15) NOT NULL,
    comment_id character varying(12) NOT NULL,
    event_type character varying(20) NOT NULL,
    event_time timestamp with time zone NOT NULL,
    CONSTRAINT chk_comment_lifecycle_event_type CHECK (((event_type)::text = ANY ((ARRAY['comment_posted'::character varying, 'comment_reported'::character varying, 'comment_removed'::character varying])::text[])))
);


--
-- Name: content_item; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.content_item (
    content_item_id character varying(13) NOT NULL,
    page_id character varying(13) NOT NULL,
    content_type character varying(10) NOT NULL,
    CONSTRAINT chk_content_item_type CHECK (((content_type)::text = ANY ((ARRAY['video'::character varying, 'file'::character varying])::text[])))
);


--
-- Name: content_item_access_period; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.content_item_access_period (
    content_item_access_period_id character varying(20) CONSTRAINT content_item_access_period_content_item_access_period__not_null NOT NULL,
    content_item_id character varying(13) NOT NULL,
    access_mode character varying(20) NOT NULL,
    valid_from timestamp with time zone NOT NULL,
    valid_to timestamp with time zone,
    CONSTRAINT chk_content_item_access_period_access_mode CHECK (((access_mode)::text = ANY ((ARRAY['public'::character varying, 'members_only'::character varying, 'restricted'::character varying])::text[]))),
    CONSTRAINT chk_content_item_access_period_valid_range CHECK (((valid_to IS NULL) OR (valid_to > valid_from)))
);


--
-- Name: feature; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feature (
    feature_id character varying(7) NOT NULL,
    feature_name character varying(50) NOT NULL
);


--
-- Name: feature_enablement_lifecycle_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feature_enablement_lifecycle_event (
    event_id character varying(14) NOT NULL,
    website_id character varying(11) NOT NULL,
    feature_id character varying(7) NOT NULL,
    event_type character varying(20) NOT NULL,
    event_time timestamp with time zone NOT NULL,
    CONSTRAINT chk_feature_enablement_event_type CHECK (((event_type)::text = ANY ((ARRAY['feature_enabled'::character varying, 'feature_disabled'::character varying])::text[])))
);


--
-- Name: invitation_outcome_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.invitation_outcome_event (
    event_id character varying(15) NOT NULL,
    invitation_id character varying(12) NOT NULL,
    event_type character varying(20) NOT NULL,
    event_time timestamp with time zone NOT NULL,
    CONSTRAINT chk_invitation_outcome_event_type CHECK (((event_type)::text = ANY ((ARRAY['rejected'::character varying, 'expired'::character varying, 'cancelled'::character varying])::text[])))
);


--
-- Name: member_profile_update_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.member_profile_update_event (
    event_id character varying(16) NOT NULL,
    member_id character varying(12) NOT NULL,
    event_time timestamp with time zone NOT NULL
);


--
-- Name: member_registration_success_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.member_registration_success_event (
    event_id character varying(15) NOT NULL,
    website_id character varying(11) NOT NULL,
    member_id character varying(12) NOT NULL,
    invitation_id character varying(12),
    registration_method character varying(20) NOT NULL,
    event_time timestamp with time zone NOT NULL,
    CONSTRAINT chk_member_registration_method CHECK (((registration_method)::text = ANY ((ARRAY['self'::character varying, 'invitation'::character varying])::text[])))
);


--
-- Name: member_state_period; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.member_state_period (
    member_state_period_id character varying(12) NOT NULL,
    member_id character varying(12) NOT NULL,
    member_state character varying(20) NOT NULL,
    valid_from timestamp with time zone NOT NULL,
    valid_to timestamp with time zone,
    CONSTRAINT chk_member_state CHECK (((member_state)::text = ANY ((ARRAY['active'::character varying, 'deactivated'::character varying, 'suspended'::character varying])::text[]))),
    CONSTRAINT chk_member_state_period_dates CHECK (((valid_to IS NULL) OR (valid_to > valid_from)))
);


--
-- Name: membership_behaviour_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.membership_behaviour_event (
    event_id character varying(16) NOT NULL,
    event_type character varying(30) NOT NULL,
    event_time timestamp with time zone NOT NULL,
    website_id character varying(11) NOT NULL,
    registration_attempt_id character varying(12),
    member_id character varying(12),
    CONSTRAINT chk_membership_behaviour_event_type CHECK (((event_type)::text = ANY ((ARRAY['member_registration_started'::character varying, 'member_registration_failed'::character varying, 'member_logged_in'::character varying])::text[])))
);


--
-- Name: membership_invitation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.membership_invitation (
    invitation_id character varying(12) NOT NULL,
    website_id character varying(11) NOT NULL,
    invitee_ref text NOT NULL,
    invitation_time timestamp with time zone NOT NULL
);


--
-- Name: page; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.page (
    page_id character varying(13) NOT NULL,
    website_id character varying(11) NOT NULL
);


--
-- Name: page_access_period; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.page_access_period (
    page_access_period_id character varying(20) NOT NULL,
    page_id character varying(13) NOT NULL,
    access_mode character varying(20) NOT NULL,
    valid_from timestamp with time zone NOT NULL,
    valid_to timestamp with time zone,
    CONSTRAINT chk_page_access_mode CHECK (((access_mode)::text = ANY ((ARRAY['public'::character varying, 'members_only'::character varying, 'restricted'::character varying])::text[]))),
    CONSTRAINT chk_page_access_period_dates CHECK (((valid_to IS NULL) OR (valid_to > valid_from)))
);


--
-- Name: payment_refund_activity_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payment_refund_activity_event (
    event_id character varying(15) NOT NULL,
    account_id character varying(10) NOT NULL,
    event_type character varying(30) NOT NULL,
    event_time timestamp with time zone NOT NULL,
    payment_ref character varying(12),
    original_payment_ref character varying(12),
    CONSTRAINT chk_payment_refund_activity_event_type CHECK (((event_type)::text = ANY ((ARRAY['payment_method_changed'::character varying, 'payment_succeeded'::character varying, 'payment_failed'::character varying, 'payment_refunded'::character varying])::text[]))),
    CONSTRAINT chk_payment_refund_reference_semantics CHECK (((((event_type)::text = 'payment_method_changed'::text) AND (payment_ref IS NULL) AND (original_payment_ref IS NULL)) OR (((event_type)::text = ANY ((ARRAY['payment_succeeded'::character varying, 'payment_failed'::character varying])::text[])) AND (payment_ref IS NOT NULL) AND (original_payment_ref IS NULL)) OR (((event_type)::text = 'payment_refunded'::text) AND (payment_ref IS NULL) AND (original_payment_ref IS NOT NULL))))
);


--
-- Name: plan_catalog; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plan_catalog (
    plan_id character varying(13) NOT NULL,
    plan_name character varying(20) NOT NULL,
    CONSTRAINT chk_plan_catalog_name CHECK (((plan_name)::text = ANY ((ARRAY['free'::character varying, 'standard'::character varying, 'premium'::character varying])::text[])))
);


--
-- Name: plan_feature_entitlement_period; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plan_feature_entitlement_period (
    entitlement_period_id character varying(8) NOT NULL,
    plan_id character varying(13) NOT NULL,
    feature_id character varying(7) NOT NULL,
    valid_from timestamp with time zone NOT NULL,
    valid_to timestamp with time zone,
    CONSTRAINT chk_entitlement_period_dates CHECK (((valid_to IS NULL) OR (valid_to > valid_from)))
);


--
-- Name: product_behaviour_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.product_behaviour_event (
    event_id character varying(17) NOT NULL,
    event_type character varying(40) NOT NULL,
    event_time timestamp with time zone NOT NULL,
    user_id character varying(10) NOT NULL,
    account_id character varying(10) NOT NULL,
    website_id character varying(11),
    feature_id character varying(7),
    CONSTRAINT chk_product_behaviour_event_type CHECK (((event_type)::text = ANY ((ARRAY['product_accessed'::character varying, 'feature_used'::character varying, 'website_analytics_viewed'::character varying, 'locked_feature_attempted'::character varying, 'restricted_product_action_attempted'::character varying])::text[])))
);


--
-- Name: rating; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rating (
    rating_id character varying(12) NOT NULL,
    member_id character varying(12) NOT NULL,
    page_id character varying(13) NOT NULL,
    rating_value integer NOT NULL,
    CONSTRAINT chk_rating_value CHECK (((rating_value >= 1) AND (rating_value <= 5)))
);


--
-- Name: rating_lifecycle_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rating_lifecycle_event (
    event_id character varying(15) NOT NULL,
    rating_id character varying(12) NOT NULL,
    event_type character varying(20) NOT NULL,
    event_time timestamp with time zone NOT NULL,
    rating_value integer,
    CONSTRAINT chk_rating_lifecycle_event_type CHECK (((event_type)::text = ANY ((ARRAY['rating_given'::character varying, 'rating_changed'::character varying, 'rating_removed'::character varying])::text[]))),
    CONSTRAINT chk_rating_lifecycle_value_range CHECK (((rating_value IS NULL) OR ((rating_value >= 1) AND (rating_value <= 5)))),
    CONSTRAINT chk_rating_lifecycle_value_semantics CHECK (((((event_type)::text = ANY ((ARRAY['rating_given'::character varying, 'rating_changed'::character varying])::text[])) AND (rating_value IS NOT NULL)) OR (((event_type)::text = 'rating_removed'::text) AND (rating_value IS NULL))))
);


--
-- Name: saas_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.saas_user (
    user_id character varying(10) NOT NULL
);


--
-- Name: session_lifecycle_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_lifecycle_event (
    event_id character varying(16) NOT NULL,
    session_id character varying(13) NOT NULL,
    event_type character varying(20) NOT NULL,
    event_time timestamp with time zone NOT NULL,
    CONSTRAINT chk_session_lifecycle_event_type CHECK (((event_type)::text = ANY ((ARRAY['session_started'::character varying, 'session_ended'::character varying])::text[])))
);


--
-- Name: session_member_attribution; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_member_attribution (
    session_member_attribution_id character varying(13) CONSTRAINT session_member_attribution_session_member_attribution__not_null NOT NULL,
    session_id character varying(13) NOT NULL,
    member_id character varying(12) NOT NULL,
    attributed_at timestamp with time zone NOT NULL
);


--
-- Name: session_traffic_attribution; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_traffic_attribution (
    session_id character varying(13) NOT NULL,
    traffic_source character varying(20) NOT NULL,
    CONSTRAINT chk_session_traffic_source CHECK (((traffic_source)::text = ANY ((ARRAY['search'::character varying, 'direct'::character varying, 'social'::character varying, 'referral'::character varying])::text[])))
);


--
-- Name: signup_journey_context; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.signup_journey_context (
    signup_journey_id character varying(9) NOT NULL,
    resulting_account_id character varying(10)
);


--
-- Name: signup_journey_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.signup_journey_event (
    event_id character varying(17) NOT NULL,
    signup_journey_id character varying(9) NOT NULL,
    event_type character varying(20) NOT NULL,
    event_time timestamp with time zone NOT NULL,
    CONSTRAINT chk_signup_journey_event_type CHECK (((event_type)::text = 'signup_started'::text))
);


--
-- Name: subscription_lifecycle_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.subscription_lifecycle_event (
    event_id character varying(15) NOT NULL,
    account_id character varying(10) NOT NULL,
    event_type character varying(30) NOT NULL,
    event_time timestamp with time zone NOT NULL,
    from_plan_id character varying(13),
    to_plan_id character varying(13),
    from_billing_cycle character varying(10),
    to_billing_cycle character varying(10),
    CONSTRAINT chk_subscription_event_billing_cycles CHECK ((((from_billing_cycle IS NULL) OR ((from_billing_cycle)::text = ANY ((ARRAY['monthly'::character varying, 'annual'::character varying])::text[]))) AND ((to_billing_cycle IS NULL) OR ((to_billing_cycle)::text = ANY ((ARRAY['monthly'::character varying, 'annual'::character varying])::text[]))))),
    CONSTRAINT chk_subscription_event_type CHECK (((event_type)::text = ANY ((ARRAY['subscription_upgraded'::character varying, 'subscription_downgraded'::character varying, 'subscription_renewed'::character varying, 'subscription_cancelled'::character varying, 'subscription_reactivated'::character varying, 'billing_cycle_changed'::character varying])::text[])))
);


--
-- Name: subscription_plan_period; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.subscription_plan_period (
    subscription_plan_period_id character varying(12) NOT NULL,
    account_id character varying(10) NOT NULL,
    plan_id character varying(13) NOT NULL,
    valid_from timestamp with time zone NOT NULL,
    valid_to timestamp with time zone,
    CONSTRAINT chk_subscription_plan_period_dates CHECK (((valid_to IS NULL) OR (valid_to > valid_from)))
);


--
-- Name: support_lifecycle_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.support_lifecycle_event (
    event_id character varying(15) NOT NULL,
    support_request_id character varying(11) NOT NULL,
    event_type character varying(30) NOT NULL,
    event_time timestamp with time zone NOT NULL,
    agent_ref text,
    CONSTRAINT chk_support_lifecycle_event_type CHECK (((event_type)::text = ANY ((ARRAY['support_request_opened'::character varying, 'support_request_resolved'::character varying])::text[])))
);


--
-- Name: support_request; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.support_request (
    support_request_id character varying(11) NOT NULL,
    account_id character varying(10) NOT NULL,
    requester_user_id character varying(10) NOT NULL,
    website_id character varying(11),
    problem_context text NOT NULL,
    agent_ref text
);


--
-- Name: user_account_membership; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_account_membership (
    membership_id character varying(11) NOT NULL,
    user_id character varying(10) NOT NULL,
    account_id character varying(10) NOT NULL
);


--
-- Name: user_account_membership_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_account_membership_event (
    event_id character varying(15) NOT NULL,
    membership_id character varying(11) NOT NULL,
    event_type character varying(20) NOT NULL,
    event_time timestamp with time zone NOT NULL,
    CONSTRAINT chk_membership_event_type CHECK (((event_type)::text = 'user_joined_account'::text))
);


--
-- Name: user_account_membership_period; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_account_membership_period (
    membership_period_id character varying(11) NOT NULL,
    membership_id character varying(11) NOT NULL,
    valid_from timestamp with time zone NOT NULL,
    valid_to timestamp with time zone,
    CONSTRAINT chk_membership_period_dates CHECK (((valid_to IS NULL) OR (valid_to > valid_from)))
);


--
-- Name: user_account_role_assignment_period; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_account_role_assignment_period (
    role_period_id character varying(11) NOT NULL,
    membership_id character varying(11) NOT NULL,
    role character varying(10) NOT NULL,
    valid_from timestamp with time zone NOT NULL,
    valid_to timestamp with time zone,
    CONSTRAINT chk_role_period_dates CHECK (((valid_to IS NULL) OR (valid_to > valid_from))),
    CONSTRAINT chk_role_period_role CHECK (((role)::text = ANY ((ARRAY['owner'::character varying, 'editor'::character varying, 'viewer'::character varying])::text[])))
);


--
-- Name: visitor; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.visitor (
    visitor_id character varying(12) NOT NULL,
    website_id character varying(11) NOT NULL
);


--
-- Name: visitor_member_linkage; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.visitor_member_linkage (
    visitor_member_link_id character varying(12) NOT NULL,
    visitor_id character varying(12) NOT NULL,
    member_id character varying(12) NOT NULL,
    valid_from timestamp with time zone NOT NULL,
    valid_to timestamp with time zone,
    CONSTRAINT chk_visitor_member_linkage_dates CHECK (((valid_to IS NULL) OR (valid_to > valid_from)))
);


--
-- Name: website; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.website (
    website_id character varying(11) NOT NULL,
    account_id character varying(10) NOT NULL,
    template_origin character varying(25) NOT NULL,
    website_purpose character varying(25) NOT NULL,
    CONSTRAINT chk_website_purpose CHECK (((website_purpose)::text = ANY ((ARRAY['portfolio_personal_brand'::character varying, 'business_services'::character varying, 'course_educational'::character varying, 'organization_nonprofit'::character varying, 'other'::character varying])::text[]))),
    CONSTRAINT chk_website_template_origin CHECK (((template_origin)::text = ANY ((ARRAY['blank'::character varying, 'portfolio_template'::character varying, 'business_template'::character varying, 'course_template'::character varying, 'organization_template'::character varying])::text[])))
);


--
-- Name: website_address_period; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.website_address_period (
    address_period_id character varying(13) NOT NULL,
    website_id character varying(11) NOT NULL,
    address_value character varying(255) NOT NULL,
    address_type character varying(20) NOT NULL,
    valid_from timestamp with time zone NOT NULL,
    valid_to timestamp with time zone,
    CONSTRAINT chk_website_address_period_type CHECK (((address_type)::text = ANY ((ARRAY['platform'::character varying, 'custom'::character varying])::text[]))),
    CONSTRAINT chk_website_address_period_valid_range CHECK (((valid_to IS NULL) OR (valid_to > valid_from)))
);


--
-- Name: website_feature_enablement_period; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.website_feature_enablement_period (
    enablement_period_id character varying(12) NOT NULL,
    website_id character varying(11) NOT NULL,
    feature_id character varying(7) NOT NULL,
    valid_from timestamp with time zone NOT NULL,
    valid_to timestamp with time zone,
    CONSTRAINT chk_enablement_period_dates CHECK (((valid_to IS NULL) OR (valid_to > valid_from)))
);


--
-- Name: website_lifecycle_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.website_lifecycle_event (
    event_id character varying(15) NOT NULL,
    website_id character varying(11) NOT NULL,
    event_type character varying(20) NOT NULL,
    event_time timestamp with time zone NOT NULL,
    CONSTRAINT chk_website_lifecycle_event_type CHECK (((event_type)::text = ANY ((ARRAY['website_created'::character varying, 'published'::character varying, 'unpublished'::character varying, 'archived'::character varying, 'restored'::character varying, 'deleted'::character varying])::text[])))
);


--
-- Name: website_live_period; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.website_live_period (
    live_period_id character varying(13) NOT NULL,
    website_id character varying(11) NOT NULL,
    valid_from timestamp with time zone NOT NULL,
    valid_to timestamp with time zone,
    CONSTRAINT chk_website_live_period_valid_range CHECK (((valid_to IS NULL) OR (valid_to > valid_from)))
);


--
-- Name: website_member; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.website_member (
    member_id character varying(12) NOT NULL,
    website_id character varying(11) NOT NULL
);


--
-- Name: account_lifecycle_event account_lifecycle_event_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_lifecycle_event
    ADD CONSTRAINT account_lifecycle_event_pkey PRIMARY KEY (event_id);


--
-- Name: account_lifecycle_period account_lifecycle_period_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_lifecycle_period
    ADD CONSTRAINT account_lifecycle_period_pkey PRIMARY KEY (account_lifecycle_period_id);


--
-- Name: account account_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account
    ADD CONSTRAINT account_pkey PRIMARY KEY (account_id);


--
-- Name: content_item content_item_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content_item
    ADD CONSTRAINT content_item_pkey PRIMARY KEY (content_item_id);


--
-- Name: billing_cycle_period excl_billing_cycle_period_no_overlap; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.billing_cycle_period
    ADD CONSTRAINT excl_billing_cycle_period_no_overlap EXCLUDE USING gist (account_id WITH =, tstzrange(valid_from, valid_to, '[)'::text) WITH &&);


--
-- Name: content_item_access_period excl_content_item_access_period_no_overlap; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content_item_access_period
    ADD CONSTRAINT excl_content_item_access_period_no_overlap EXCLUDE USING gist (content_item_id WITH =, tstzrange(valid_from, valid_to, '[)'::text) WITH &&);


--
-- Name: member_state_period excl_member_state_period_no_overlap; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_state_period
    ADD CONSTRAINT excl_member_state_period_no_overlap EXCLUDE USING gist (member_id WITH =, tstzrange(valid_from, valid_to, '[)'::text) WITH &&);


--
-- Name: page_access_period excl_page_access_period_no_overlap; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.page_access_period
    ADD CONSTRAINT excl_page_access_period_no_overlap EXCLUDE USING gist (page_id WITH =, tstzrange(valid_from, valid_to, '[)'::text) WITH &&);


--
-- Name: plan_feature_entitlement_period excl_plan_feature_entitlement_period_no_overlap; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_feature_entitlement_period
    ADD CONSTRAINT excl_plan_feature_entitlement_period_no_overlap EXCLUDE USING gist (plan_id WITH =, feature_id WITH =, tstzrange(valid_from, valid_to, '[)'::text) WITH &&);


--
-- Name: subscription_plan_period excl_subscription_plan_period_no_overlap; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscription_plan_period
    ADD CONSTRAINT excl_subscription_plan_period_no_overlap EXCLUDE USING gist (account_id WITH =, tstzrange(valid_from, valid_to, '[)'::text) WITH &&);


--
-- Name: user_account_membership_period excl_user_account_membership_period_no_overlap; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account_membership_period
    ADD CONSTRAINT excl_user_account_membership_period_no_overlap EXCLUDE USING gist (membership_id WITH =, tstzrange(valid_from, valid_to, '[)'::text) WITH &&);


--
-- Name: user_account_role_assignment_period excl_user_account_role_assignment_period_no_overlap; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account_role_assignment_period
    ADD CONSTRAINT excl_user_account_role_assignment_period_no_overlap EXCLUDE USING gist (membership_id WITH =, tstzrange(valid_from, valid_to, '[)'::text) WITH &&);


--
-- Name: website_feature_enablement_period excl_website_feature_enablement_period_no_overlap; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.website_feature_enablement_period
    ADD CONSTRAINT excl_website_feature_enablement_period_no_overlap EXCLUDE USING gist (website_id WITH =, feature_id WITH =, tstzrange(valid_from, valid_to, '[)'::text) WITH &&);


--
-- Name: website_live_period excl_website_live_period_no_overlap; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.website_live_period
    ADD CONSTRAINT excl_website_live_period_no_overlap EXCLUDE USING gist (website_id WITH =, tstzrange(valid_from, valid_to, '[)'::text) WITH &&);


--
-- Name: page_access_period page_access_period_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.page_access_period
    ADD CONSTRAINT page_access_period_pkey PRIMARY KEY (page_access_period_id);


--
-- Name: page page_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.page
    ADD CONSTRAINT page_pkey PRIMARY KEY (page_id);


--
-- Name: acquisition_source_attribution pk_acquisition_source_attribution; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acquisition_source_attribution
    ADD CONSTRAINT pk_acquisition_source_attribution PRIMARY KEY (signup_journey_id);


--
-- Name: audience_interaction_event pk_audience_interaction_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audience_interaction_event
    ADD CONSTRAINT pk_audience_interaction_event PRIMARY KEY (event_id);


--
-- Name: audience_session pk_audience_session; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audience_session
    ADD CONSTRAINT pk_audience_session PRIMARY KEY (session_id);


--
-- Name: billing_cycle_period pk_billing_cycle_period; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.billing_cycle_period
    ADD CONSTRAINT pk_billing_cycle_period PRIMARY KEY (billing_cycle_period_id);


--
-- Name: comment pk_comment; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comment
    ADD CONSTRAINT pk_comment PRIMARY KEY (comment_id);


--
-- Name: comment_lifecycle_event pk_comment_lifecycle_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comment_lifecycle_event
    ADD CONSTRAINT pk_comment_lifecycle_event PRIMARY KEY (event_id);


--
-- Name: content_item_access_period pk_content_item_access_period; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content_item_access_period
    ADD CONSTRAINT pk_content_item_access_period PRIMARY KEY (content_item_access_period_id);


--
-- Name: feature pk_feature; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature
    ADD CONSTRAINT pk_feature PRIMARY KEY (feature_id);


--
-- Name: feature_enablement_lifecycle_event pk_feature_enablement_lifecycle_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_enablement_lifecycle_event
    ADD CONSTRAINT pk_feature_enablement_lifecycle_event PRIMARY KEY (event_id);


--
-- Name: invitation_outcome_event pk_invitation_outcome_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invitation_outcome_event
    ADD CONSTRAINT pk_invitation_outcome_event PRIMARY KEY (event_id);


--
-- Name: member_profile_update_event pk_member_profile_update_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_profile_update_event
    ADD CONSTRAINT pk_member_profile_update_event PRIMARY KEY (event_id);


--
-- Name: member_registration_success_event pk_member_registration_success_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_registration_success_event
    ADD CONSTRAINT pk_member_registration_success_event PRIMARY KEY (event_id);


--
-- Name: member_state_period pk_member_state_period; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_state_period
    ADD CONSTRAINT pk_member_state_period PRIMARY KEY (member_state_period_id);


--
-- Name: membership_behaviour_event pk_membership_behaviour_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.membership_behaviour_event
    ADD CONSTRAINT pk_membership_behaviour_event PRIMARY KEY (event_id);


--
-- Name: membership_invitation pk_membership_invitation; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.membership_invitation
    ADD CONSTRAINT pk_membership_invitation PRIMARY KEY (invitation_id);


--
-- Name: payment_refund_activity_event pk_payment_refund_activity_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_refund_activity_event
    ADD CONSTRAINT pk_payment_refund_activity_event PRIMARY KEY (event_id);


--
-- Name: plan_catalog pk_plan_catalog; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_catalog
    ADD CONSTRAINT pk_plan_catalog PRIMARY KEY (plan_id);


--
-- Name: plan_feature_entitlement_period pk_plan_feature_entitlement_period; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_feature_entitlement_period
    ADD CONSTRAINT pk_plan_feature_entitlement_period PRIMARY KEY (entitlement_period_id);


--
-- Name: product_behaviour_event pk_product_behaviour_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_behaviour_event
    ADD CONSTRAINT pk_product_behaviour_event PRIMARY KEY (event_id);


--
-- Name: rating pk_rating; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rating
    ADD CONSTRAINT pk_rating PRIMARY KEY (rating_id);


--
-- Name: rating_lifecycle_event pk_rating_lifecycle_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rating_lifecycle_event
    ADD CONSTRAINT pk_rating_lifecycle_event PRIMARY KEY (event_id);


--
-- Name: session_lifecycle_event pk_session_lifecycle_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_lifecycle_event
    ADD CONSTRAINT pk_session_lifecycle_event PRIMARY KEY (event_id);


--
-- Name: session_member_attribution pk_session_member_attribution; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_member_attribution
    ADD CONSTRAINT pk_session_member_attribution PRIMARY KEY (session_member_attribution_id);


--
-- Name: session_traffic_attribution pk_session_traffic_attribution; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_traffic_attribution
    ADD CONSTRAINT pk_session_traffic_attribution PRIMARY KEY (session_id);


--
-- Name: signup_journey_context pk_signup_journey_context; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.signup_journey_context
    ADD CONSTRAINT pk_signup_journey_context PRIMARY KEY (signup_journey_id);


--
-- Name: signup_journey_event pk_signup_journey_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.signup_journey_event
    ADD CONSTRAINT pk_signup_journey_event PRIMARY KEY (event_id);


--
-- Name: subscription_lifecycle_event pk_subscription_lifecycle_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscription_lifecycle_event
    ADD CONSTRAINT pk_subscription_lifecycle_event PRIMARY KEY (event_id);


--
-- Name: subscription_plan_period pk_subscription_plan_period; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscription_plan_period
    ADD CONSTRAINT pk_subscription_plan_period PRIMARY KEY (subscription_plan_period_id);


--
-- Name: support_lifecycle_event pk_support_lifecycle_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.support_lifecycle_event
    ADD CONSTRAINT pk_support_lifecycle_event PRIMARY KEY (event_id);


--
-- Name: support_request pk_support_request; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.support_request
    ADD CONSTRAINT pk_support_request PRIMARY KEY (support_request_id);


--
-- Name: visitor pk_visitor; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visitor
    ADD CONSTRAINT pk_visitor PRIMARY KEY (visitor_id);


--
-- Name: visitor_member_linkage pk_visitor_member_linkage; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visitor_member_linkage
    ADD CONSTRAINT pk_visitor_member_linkage PRIMARY KEY (visitor_member_link_id);


--
-- Name: website_address_period pk_website_address_period; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.website_address_period
    ADD CONSTRAINT pk_website_address_period PRIMARY KEY (address_period_id);


--
-- Name: website_feature_enablement_period pk_website_feature_enablement_period; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.website_feature_enablement_period
    ADD CONSTRAINT pk_website_feature_enablement_period PRIMARY KEY (enablement_period_id);


--
-- Name: website_lifecycle_event pk_website_lifecycle_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.website_lifecycle_event
    ADD CONSTRAINT pk_website_lifecycle_event PRIMARY KEY (event_id);


--
-- Name: website_live_period pk_website_live_period; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.website_live_period
    ADD CONSTRAINT pk_website_live_period PRIMARY KEY (live_period_id);


--
-- Name: website_member pk_website_member; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.website_member
    ADD CONSTRAINT pk_website_member PRIMARY KEY (member_id);


--
-- Name: saas_user saas_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saas_user
    ADD CONSTRAINT saas_user_pkey PRIMARY KEY (user_id);


--
-- Name: feature uq_feature_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature
    ADD CONSTRAINT uq_feature_name UNIQUE (feature_name);


--
-- Name: user_account_membership uq_membership_user_account; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account_membership
    ADD CONSTRAINT uq_membership_user_account UNIQUE (user_id, account_id);


--
-- Name: payment_refund_activity_event uq_payment_refund_activity_payment_ref; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_refund_activity_event
    ADD CONSTRAINT uq_payment_refund_activity_payment_ref UNIQUE (payment_ref);


--
-- Name: plan_catalog uq_plan_catalog_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_catalog
    ADD CONSTRAINT uq_plan_catalog_name UNIQUE (plan_name);


--
-- Name: session_lifecycle_event uq_session_lifecycle_event_type; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_lifecycle_event
    ADD CONSTRAINT uq_session_lifecycle_event_type UNIQUE (session_id, event_type);


--
-- Name: session_member_attribution uq_session_member_attribution_session; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_member_attribution
    ADD CONSTRAINT uq_session_member_attribution_session UNIQUE (session_id);


--
-- Name: signup_journey_event uq_signup_journey_event_journey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.signup_journey_event
    ADD CONSTRAINT uq_signup_journey_event_journey UNIQUE (signup_journey_id);


--
-- Name: signup_journey_context uq_signup_journey_resulting_account; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.signup_journey_context
    ADD CONSTRAINT uq_signup_journey_resulting_account UNIQUE (resulting_account_id);


--
-- Name: support_lifecycle_event uq_support_lifecycle_event_type; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.support_lifecycle_event
    ADD CONSTRAINT uq_support_lifecycle_event_type UNIQUE (support_request_id, event_type);


--
-- Name: visitor_member_linkage uq_visitor_member_linkage_member; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visitor_member_linkage
    ADD CONSTRAINT uq_visitor_member_linkage_member UNIQUE (member_id);


--
-- Name: visitor_member_linkage uq_visitor_member_linkage_visitor; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visitor_member_linkage
    ADD CONSTRAINT uq_visitor_member_linkage_visitor UNIQUE (visitor_id);


--
-- Name: user_account_membership_event user_account_membership_event_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account_membership_event
    ADD CONSTRAINT user_account_membership_event_pkey PRIMARY KEY (event_id);


--
-- Name: user_account_membership_period user_account_membership_period_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account_membership_period
    ADD CONSTRAINT user_account_membership_period_pkey PRIMARY KEY (membership_period_id);


--
-- Name: user_account_membership user_account_membership_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account_membership
    ADD CONSTRAINT user_account_membership_pkey PRIMARY KEY (membership_id);


--
-- Name: user_account_role_assignment_period user_account_role_assignment_period_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account_role_assignment_period
    ADD CONSTRAINT user_account_role_assignment_period_pkey PRIMARY KEY (role_period_id);


--
-- Name: website website_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.website
    ADD CONSTRAINT website_pkey PRIMARY KEY (website_id);


--
-- Name: comment trg_comment_same_website; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_comment_same_website BEFORE INSERT OR UPDATE OF member_id, page_id ON public.comment FOR EACH ROW EXECUTE FUNCTION public.enforce_contribution_same_website();


--
-- Name: website_member trg_member_website_move_guard; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_member_website_move_guard BEFORE UPDATE OF website_id ON public.website_member FOR EACH ROW WHEN (((old.website_id)::text IS DISTINCT FROM (new.website_id)::text)) EXECUTE FUNCTION public.guard_contribution_parent_website_change();


--
-- Name: page trg_page_website_move_guard; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_page_website_move_guard BEFORE UPDATE OF website_id ON public.page FOR EACH ROW WHEN (((old.website_id)::text IS DISTINCT FROM (new.website_id)::text)) EXECUTE FUNCTION public.guard_contribution_parent_website_change();


--
-- Name: rating trg_rating_same_website; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_rating_same_website BEFORE INSERT OR UPDATE OF member_id, page_id ON public.rating FOR EACH ROW EXECUTE FUNCTION public.enforce_contribution_same_website();


--
-- Name: payment_refund_activity_event trg_refund_provenance; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_refund_provenance BEFORE INSERT OR UPDATE OF account_id, event_type, event_time, original_payment_ref ON public.payment_refund_activity_event FOR EACH ROW EXECUTE FUNCTION public.enforce_refund_provenance();


--
-- Name: payment_refund_activity_event trg_refunded_payment_mutation_guard; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_refunded_payment_mutation_guard BEFORE UPDATE OF payment_ref, account_id, event_type, event_time ON public.payment_refund_activity_event FOR EACH ROW EXECUTE FUNCTION public.guard_refunded_payment_mutation();


--
-- Name: account_lifecycle_event fk_account_lifecycle_event_account; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_lifecycle_event
    ADD CONSTRAINT fk_account_lifecycle_event_account FOREIGN KEY (account_id) REFERENCES public.account(account_id);


--
-- Name: account_lifecycle_period fk_account_lifecycle_period_account; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_lifecycle_period
    ADD CONSTRAINT fk_account_lifecycle_period_account FOREIGN KEY (account_id) REFERENCES public.account(account_id);


--
-- Name: acquisition_source_attribution fk_acquisition_source_signup_journey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acquisition_source_attribution
    ADD CONSTRAINT fk_acquisition_source_signup_journey FOREIGN KEY (signup_journey_id) REFERENCES public.signup_journey_context(signup_journey_id);


--
-- Name: audience_interaction_event fk_audience_interaction_event_content; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audience_interaction_event
    ADD CONSTRAINT fk_audience_interaction_event_content FOREIGN KEY (content_item_id) REFERENCES public.content_item(content_item_id);


--
-- Name: audience_interaction_event fk_audience_interaction_event_page; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audience_interaction_event
    ADD CONSTRAINT fk_audience_interaction_event_page FOREIGN KEY (page_id) REFERENCES public.page(page_id);


--
-- Name: audience_interaction_event fk_audience_interaction_event_session; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audience_interaction_event
    ADD CONSTRAINT fk_audience_interaction_event_session FOREIGN KEY (session_id) REFERENCES public.audience_session(session_id);


--
-- Name: audience_session fk_audience_session_visitor; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audience_session
    ADD CONSTRAINT fk_audience_session_visitor FOREIGN KEY (visitor_id) REFERENCES public.visitor(visitor_id);


--
-- Name: audience_session fk_audience_session_website; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audience_session
    ADD CONSTRAINT fk_audience_session_website FOREIGN KEY (website_id) REFERENCES public.website(website_id);


--
-- Name: billing_cycle_period fk_billing_cycle_period_account; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.billing_cycle_period
    ADD CONSTRAINT fk_billing_cycle_period_account FOREIGN KEY (account_id) REFERENCES public.account(account_id);


--
-- Name: comment_lifecycle_event fk_comment_lifecycle_event_comment; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comment_lifecycle_event
    ADD CONSTRAINT fk_comment_lifecycle_event_comment FOREIGN KEY (comment_id) REFERENCES public.comment(comment_id);


--
-- Name: comment fk_comment_member; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comment
    ADD CONSTRAINT fk_comment_member FOREIGN KEY (member_id) REFERENCES public.website_member(member_id);


--
-- Name: comment fk_comment_page; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comment
    ADD CONSTRAINT fk_comment_page FOREIGN KEY (page_id) REFERENCES public.page(page_id);


--
-- Name: content_item_access_period fk_content_item_access_period_content_item; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content_item_access_period
    ADD CONSTRAINT fk_content_item_access_period_content_item FOREIGN KEY (content_item_id) REFERENCES public.content_item(content_item_id);


--
-- Name: content_item fk_content_item_page; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content_item
    ADD CONSTRAINT fk_content_item_page FOREIGN KEY (page_id) REFERENCES public.page(page_id);


--
-- Name: website_feature_enablement_period fk_enablement_period_feature; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.website_feature_enablement_period
    ADD CONSTRAINT fk_enablement_period_feature FOREIGN KEY (feature_id) REFERENCES public.feature(feature_id);


--
-- Name: website_feature_enablement_period fk_enablement_period_website; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.website_feature_enablement_period
    ADD CONSTRAINT fk_enablement_period_website FOREIGN KEY (website_id) REFERENCES public.website(website_id);


--
-- Name: plan_feature_entitlement_period fk_entitlement_period_feature; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_feature_entitlement_period
    ADD CONSTRAINT fk_entitlement_period_feature FOREIGN KEY (feature_id) REFERENCES public.feature(feature_id);


--
-- Name: plan_feature_entitlement_period fk_entitlement_period_plan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_feature_entitlement_period
    ADD CONSTRAINT fk_entitlement_period_plan FOREIGN KEY (plan_id) REFERENCES public.plan_catalog(plan_id);


--
-- Name: feature_enablement_lifecycle_event fk_feature_enablement_event_feature; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_enablement_lifecycle_event
    ADD CONSTRAINT fk_feature_enablement_event_feature FOREIGN KEY (feature_id) REFERENCES public.feature(feature_id);


--
-- Name: feature_enablement_lifecycle_event fk_feature_enablement_event_website; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_enablement_lifecycle_event
    ADD CONSTRAINT fk_feature_enablement_event_website FOREIGN KEY (website_id) REFERENCES public.website(website_id);


--
-- Name: invitation_outcome_event fk_invitation_outcome_event_invitation; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invitation_outcome_event
    ADD CONSTRAINT fk_invitation_outcome_event_invitation FOREIGN KEY (invitation_id) REFERENCES public.membership_invitation(invitation_id);


--
-- Name: member_profile_update_event fk_member_profile_update_event_member; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_profile_update_event
    ADD CONSTRAINT fk_member_profile_update_event_member FOREIGN KEY (member_id) REFERENCES public.website_member(member_id);


--
-- Name: member_registration_success_event fk_member_registration_success_event_invitation; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_registration_success_event
    ADD CONSTRAINT fk_member_registration_success_event_invitation FOREIGN KEY (invitation_id) REFERENCES public.membership_invitation(invitation_id);


--
-- Name: member_registration_success_event fk_member_registration_success_event_member; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_registration_success_event
    ADD CONSTRAINT fk_member_registration_success_event_member FOREIGN KEY (member_id) REFERENCES public.website_member(member_id);


--
-- Name: member_registration_success_event fk_member_registration_success_event_website; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_registration_success_event
    ADD CONSTRAINT fk_member_registration_success_event_website FOREIGN KEY (website_id) REFERENCES public.website(website_id);


--
-- Name: member_state_period fk_member_state_period_member; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_state_period
    ADD CONSTRAINT fk_member_state_period_member FOREIGN KEY (member_id) REFERENCES public.website_member(member_id);


--
-- Name: user_account_membership fk_membership_account; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account_membership
    ADD CONSTRAINT fk_membership_account FOREIGN KEY (account_id) REFERENCES public.account(account_id);


--
-- Name: membership_behaviour_event fk_membership_behaviour_event_member; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.membership_behaviour_event
    ADD CONSTRAINT fk_membership_behaviour_event_member FOREIGN KEY (member_id) REFERENCES public.website_member(member_id);


--
-- Name: membership_behaviour_event fk_membership_behaviour_event_website; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.membership_behaviour_event
    ADD CONSTRAINT fk_membership_behaviour_event_website FOREIGN KEY (website_id) REFERENCES public.website(website_id);


--
-- Name: user_account_membership_event fk_membership_event_membership; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account_membership_event
    ADD CONSTRAINT fk_membership_event_membership FOREIGN KEY (membership_id) REFERENCES public.user_account_membership(membership_id);


--
-- Name: membership_invitation fk_membership_invitation_website; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.membership_invitation
    ADD CONSTRAINT fk_membership_invitation_website FOREIGN KEY (website_id) REFERENCES public.website(website_id);


--
-- Name: user_account_membership_period fk_membership_period_membership; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account_membership_period
    ADD CONSTRAINT fk_membership_period_membership FOREIGN KEY (membership_id) REFERENCES public.user_account_membership(membership_id);


--
-- Name: user_account_membership fk_membership_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account_membership
    ADD CONSTRAINT fk_membership_user FOREIGN KEY (user_id) REFERENCES public.saas_user(user_id);


--
-- Name: page_access_period fk_page_access_period_page; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.page_access_period
    ADD CONSTRAINT fk_page_access_period_page FOREIGN KEY (page_id) REFERENCES public.page(page_id);


--
-- Name: page fk_page_website; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.page
    ADD CONSTRAINT fk_page_website FOREIGN KEY (website_id) REFERENCES public.website(website_id);


--
-- Name: payment_refund_activity_event fk_payment_refund_activity_account; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_refund_activity_event
    ADD CONSTRAINT fk_payment_refund_activity_account FOREIGN KEY (account_id) REFERENCES public.account(account_id);


--
-- Name: payment_refund_activity_event fk_payment_refund_original_payment; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_refund_activity_event
    ADD CONSTRAINT fk_payment_refund_original_payment FOREIGN KEY (original_payment_ref) REFERENCES public.payment_refund_activity_event(payment_ref);


--
-- Name: product_behaviour_event fk_product_behaviour_event_account; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_behaviour_event
    ADD CONSTRAINT fk_product_behaviour_event_account FOREIGN KEY (account_id) REFERENCES public.account(account_id);


--
-- Name: product_behaviour_event fk_product_behaviour_event_feature; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_behaviour_event
    ADD CONSTRAINT fk_product_behaviour_event_feature FOREIGN KEY (feature_id) REFERENCES public.feature(feature_id);


--
-- Name: product_behaviour_event fk_product_behaviour_event_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_behaviour_event
    ADD CONSTRAINT fk_product_behaviour_event_user FOREIGN KEY (user_id) REFERENCES public.saas_user(user_id);


--
-- Name: product_behaviour_event fk_product_behaviour_event_website; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_behaviour_event
    ADD CONSTRAINT fk_product_behaviour_event_website FOREIGN KEY (website_id) REFERENCES public.website(website_id);


--
-- Name: rating_lifecycle_event fk_rating_lifecycle_event_rating; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rating_lifecycle_event
    ADD CONSTRAINT fk_rating_lifecycle_event_rating FOREIGN KEY (rating_id) REFERENCES public.rating(rating_id);


--
-- Name: rating fk_rating_member; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rating
    ADD CONSTRAINT fk_rating_member FOREIGN KEY (member_id) REFERENCES public.website_member(member_id);


--
-- Name: rating fk_rating_page; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rating
    ADD CONSTRAINT fk_rating_page FOREIGN KEY (page_id) REFERENCES public.page(page_id);


--
-- Name: user_account_role_assignment_period fk_role_period_membership; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account_role_assignment_period
    ADD CONSTRAINT fk_role_period_membership FOREIGN KEY (membership_id) REFERENCES public.user_account_membership(membership_id);


--
-- Name: session_lifecycle_event fk_session_lifecycle_event_session; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_lifecycle_event
    ADD CONSTRAINT fk_session_lifecycle_event_session FOREIGN KEY (session_id) REFERENCES public.audience_session(session_id);


--
-- Name: session_member_attribution fk_session_member_attribution_member; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_member_attribution
    ADD CONSTRAINT fk_session_member_attribution_member FOREIGN KEY (member_id) REFERENCES public.website_member(member_id);


--
-- Name: session_member_attribution fk_session_member_attribution_session; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_member_attribution
    ADD CONSTRAINT fk_session_member_attribution_session FOREIGN KEY (session_id) REFERENCES public.audience_session(session_id);


--
-- Name: session_traffic_attribution fk_session_traffic_attribution_session; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_traffic_attribution
    ADD CONSTRAINT fk_session_traffic_attribution_session FOREIGN KEY (session_id) REFERENCES public.audience_session(session_id);


--
-- Name: signup_journey_event fk_signup_journey_event_context; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.signup_journey_event
    ADD CONSTRAINT fk_signup_journey_event_context FOREIGN KEY (signup_journey_id) REFERENCES public.signup_journey_context(signup_journey_id);


--
-- Name: signup_journey_context fk_signup_journey_resulting_account; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.signup_journey_context
    ADD CONSTRAINT fk_signup_journey_resulting_account FOREIGN KEY (resulting_account_id) REFERENCES public.account(account_id);


--
-- Name: subscription_lifecycle_event fk_subscription_event_account; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscription_lifecycle_event
    ADD CONSTRAINT fk_subscription_event_account FOREIGN KEY (account_id) REFERENCES public.account(account_id);


--
-- Name: subscription_lifecycle_event fk_subscription_event_from_plan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscription_lifecycle_event
    ADD CONSTRAINT fk_subscription_event_from_plan FOREIGN KEY (from_plan_id) REFERENCES public.plan_catalog(plan_id);


--
-- Name: subscription_lifecycle_event fk_subscription_event_to_plan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscription_lifecycle_event
    ADD CONSTRAINT fk_subscription_event_to_plan FOREIGN KEY (to_plan_id) REFERENCES public.plan_catalog(plan_id);


--
-- Name: subscription_plan_period fk_subscription_plan_period_account; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscription_plan_period
    ADD CONSTRAINT fk_subscription_plan_period_account FOREIGN KEY (account_id) REFERENCES public.account(account_id);


--
-- Name: subscription_plan_period fk_subscription_plan_period_plan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscription_plan_period
    ADD CONSTRAINT fk_subscription_plan_period_plan FOREIGN KEY (plan_id) REFERENCES public.plan_catalog(plan_id);


--
-- Name: support_lifecycle_event fk_support_lifecycle_event_request; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.support_lifecycle_event
    ADD CONSTRAINT fk_support_lifecycle_event_request FOREIGN KEY (support_request_id) REFERENCES public.support_request(support_request_id);


--
-- Name: support_request fk_support_request_account; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.support_request
    ADD CONSTRAINT fk_support_request_account FOREIGN KEY (account_id) REFERENCES public.account(account_id);


--
-- Name: support_request fk_support_request_requester; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.support_request
    ADD CONSTRAINT fk_support_request_requester FOREIGN KEY (requester_user_id) REFERENCES public.saas_user(user_id);


--
-- Name: support_request fk_support_request_website; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.support_request
    ADD CONSTRAINT fk_support_request_website FOREIGN KEY (website_id) REFERENCES public.website(website_id);


--
-- Name: visitor_member_linkage fk_visitor_member_linkage_member; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visitor_member_linkage
    ADD CONSTRAINT fk_visitor_member_linkage_member FOREIGN KEY (member_id) REFERENCES public.website_member(member_id);


--
-- Name: visitor_member_linkage fk_visitor_member_linkage_visitor; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visitor_member_linkage
    ADD CONSTRAINT fk_visitor_member_linkage_visitor FOREIGN KEY (visitor_id) REFERENCES public.visitor(visitor_id);


--
-- Name: visitor fk_visitor_website; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visitor
    ADD CONSTRAINT fk_visitor_website FOREIGN KEY (website_id) REFERENCES public.website(website_id);


--
-- Name: website fk_website_account; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.website
    ADD CONSTRAINT fk_website_account FOREIGN KEY (account_id) REFERENCES public.account(account_id);


--
-- Name: website_address_period fk_website_address_period_website; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.website_address_period
    ADD CONSTRAINT fk_website_address_period_website FOREIGN KEY (website_id) REFERENCES public.website(website_id);


--
-- Name: website_lifecycle_event fk_website_lifecycle_event_website; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.website_lifecycle_event
    ADD CONSTRAINT fk_website_lifecycle_event_website FOREIGN KEY (website_id) REFERENCES public.website(website_id);


--
-- Name: website_live_period fk_website_live_period_website; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.website_live_period
    ADD CONSTRAINT fk_website_live_period_website FOREIGN KEY (website_id) REFERENCES public.website(website_id);


--
-- Name: website_member fk_website_member_website; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.website_member
    ADD CONSTRAINT fk_website_member_website FOREIGN KEY (website_id) REFERENCES public.website(website_id);


--
-- PostgreSQL database dump complete
--

\unrestrict BfkigsQ2bOO2netHBf93FfWUCaWZob4ytya85NZDre75fsczetBcCvuXiUm5yLp

