"""Política pura de classificação; NÃO valida assinatura Google nem sessão Supabase.

Somente um backend verificador de OIDC/sessão pode instanciar VerifiedGoogleIdentity
com dados comprovados. Nunca chame classify_google_identity com JSON do navegador.
O resultado sempre inicia PENDING e não concede escola, papel ou participação.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class IdentityPolicyError(ValueError):
    """Falha fechada; códigos estáveis, sem ecoar PII de contas."""


class GoogleAccountKind(str, Enum):
    PERSONAL_GMAIL = "PERSONAL_GMAIL"
    WORKSPACE = "WORKSPACE"


class EnrollmentStatus(str, Enum):
    PENDING = "PENDING"


@dataclass(frozen=True, slots=True)
class VerifiedGoogleIdentity:
    """Dados exclusivamente produzidos por verificador Google OIDC confiável.

    provider_sub corresponde ao claim Google 'sub', não ao e-mail.
    hosted_domain deve vir de claim Google 'hd' verificado, nunca de request hint.
    """

    provider: str
    provider_sub: str
    email: str
    email_verified: bool
    hosted_domain: str | None


@dataclass(frozen=True, slots=True)
class GoogleAccountEligibility:
    """Elegibilidade de autenticação NÃO é autorização para competir."""

    account_kind: GoogleAccountKind
    enrollment_status: EnrollmentStatus = EnrollmentStatus.PENDING


_LABEL_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")
_LOCAL_RE = re.compile(r"[a-zA-Z0-9.!#$%&'*+/=?^_\x60{|}~-]{1,64}\Z")


def _email_domain(email: str) -> str:
    if type(email) is not str or len(email) > 254 or email.count("@") != 1:
        raise IdentityPolicyError("GOOGLE_EMAIL_INVALID")
    local, domain = email.split("@", 1)
    if not _LOCAL_RE.fullmatch(local) or local.startswith(".") or local.endswith(".") or ".." in local:
        raise IdentityPolicyError("GOOGLE_EMAIL_INVALID")
    return _dns_domain(domain, "GOOGLE_EMAIL_INVALID")


def _dns_domain(domain: str, error: str) -> str:
    if type(domain) is not str or len(domain) > 253:
        raise IdentityPolicyError(error)
    normalized = domain.lower()
    labels = normalized.split(".")
    if len(labels) < 2 or any(not _LABEL_RE.fullmatch(label) for label in labels):
        raise IdentityPolicyError(error)
    return normalized


def classify_google_identity(identity: VerifiedGoogleIdentity) -> GoogleAccountEligibility:
    """Classifica conta pessoal/Workspace já verificada; SEM acesso a recursos.

    A verificação de assinatura, issuer/audience/expiry, origem Google e correlação
    com auth.users.id deve ocorrer ANTES desta chamada, fora desta função pura.
    """
    if type(identity) is not VerifiedGoogleIdentity:
        raise IdentityPolicyError("VERIFIED_IDENTITY_REQUIRED")
    if identity.provider != "google":
        raise IdentityPolicyError("GOOGLE_PROVIDER_REQUIRED")
    subject = identity.provider_sub
    if type(subject) is not str or not 1 <= len(subject) <= 255 or not subject.isascii() or not subject.isprintable() or any(char.isspace() for char in subject):
        raise IdentityPolicyError("GOOGLE_SUB_INVALID")
    if identity.email_verified is not True:
        raise IdentityPolicyError("GOOGLE_EMAIL_UNVERIFIED")

    domain = _email_domain(identity.email)
    if identity.hosted_domain is None:
        if domain != "gmail.com":
            # Google Account pessoal com outro provedor de e-mail é pós-MVP.
            # E-mail acadêmico sem hd NÃO prova Workspace.
            raise IdentityPolicyError("GOOGLE_ACCOUNT_UNSUPPORTED")
        return GoogleAccountEligibility(GoogleAccountKind.PERSONAL_GMAIL)

    hosted = _dns_domain(identity.hosted_domain, "GOOGLE_HD_INVALID")
    if hosted == "gmail.com" or domain == "gmail.com":
        raise IdentityPolicyError("GOOGLE_IDENTITY_INCONSISTENT")
    return GoogleAccountEligibility(GoogleAccountKind.WORKSPACE)
